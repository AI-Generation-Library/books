package com.example.reservation;
import java.io.IOException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.UnexpectedRollbackException;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties = {"app.demo-password=test-only-password", "spring.datasource.url=jdbc:h2:mem:transactions;DB_CLOSE_DELAY=-1"})
@Import(TransactionTests.Config.class)
class TransactionTests {
    @Autowired Outer outer;
    @Autowired Inner inner;
    @Autowired JdbcTemplate jdbc;
    @BeforeEach void reset() { jdbc.update("DELETE FROM audit_log"); }
    int rows() { return jdbc.queryForObject("SELECT COUNT(*) FROM audit_log", Integer.class); }
    @Test void externalInvocationIsTransactional() { assertTrue(inner.active()); }
    @Test void selfInvocationDoesNotStartTransaction() { assertFalse(inner.self()); }
    @Test void uncheckedExceptionRollsBack() {
        assertThrows(IllegalStateException.class, () -> inner.requiredFailure()); assertEquals(0, rows());
    }
    @Test void checkedExceptionCommitsByDefault() {
        assertThrows(IOException.class, () -> inner.checked()); assertEquals(1, rows());
    }
    @Test void rollbackForIncludesCheckedException() {
        assertThrows(IOException.class, () -> inner.checkedRollback()); assertEquals(0, rows());
    }
    @Test void catchingLocallyCanCommit() { inner.swallow(); assertEquals(1, rows()); }
    @Test void catchingInnerRequiredCannotUndoRollbackOnly() {
        assertThrows(UnexpectedRollbackException.class, () -> outer.catchRequired()); assertEquals(0, rows());
    }
    @Test void requiresNewCommitSurvivesOuterRollback() {
        assertThrows(IllegalStateException.class, () -> outer.failAfterAudit()); assertEquals(1, rows());
        assertEquals("independent", jdbc.queryForObject("SELECT message FROM audit_log", String.class));
    }
    @TestConfiguration(proxyBeanMethods = false)
    static class Config {
        @Bean Inner inner(JdbcTemplate jdbc) { return new Inner(jdbc); }
        @Bean Outer outer(JdbcTemplate jdbc, Inner inner) { return new Outer(jdbc, inner); }
    }
    public static class Inner {
        private final JdbcTemplate jdbc;
        public Inner(JdbcTemplate jdbc) { this.jdbc = jdbc; }
        void insert(String text) { jdbc.update("INSERT INTO audit_log(message) VALUES (?)", text); }
        @Transactional public boolean active() { return TransactionSynchronizationManager.isActualTransactionActive(); }
        public boolean self() { return active(); }
        @Transactional public void requiredFailure() { insert("required"); throw new IllegalStateException("fail"); }
        @Transactional public void checked() throws IOException { insert("checked"); throw new IOException("fail"); }
        @Transactional(rollbackFor = IOException.class)
        public void checkedRollback() throws IOException { insert("checked"); throw new IOException("fail"); }
        @Transactional public void swallow() {
            insert("swallowed");
            try { throw new IllegalStateException("fail"); } catch (IllegalStateException ignored) { }
        }
        @Transactional(propagation = Propagation.REQUIRES_NEW)
        public void independent() { insert("independent"); }
    }
    public static class Outer {
        private final JdbcTemplate jdbc;
        private final Inner inner;
        public Outer(JdbcTemplate jdbc, Inner inner) { this.jdbc = jdbc; this.inner = inner; }
        @Transactional public void catchRequired() {
            try { inner.requiredFailure(); } catch (IllegalStateException ignored) { }
        }
        @Transactional public void failAfterAudit() {
            jdbc.update("INSERT INTO audit_log(message) VALUES (?)", "outer");
            inner.independent(); throw new IllegalStateException("outer failed");
        }
    }
}
