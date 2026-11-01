package com.example.reservation;
import java.util.ArrayList;
import java.util.concurrent.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(properties = {"app.demo-password=test-only-password", "spring.datasource.url=jdbc:h2:mem:service;DB_CLOSE_DELAY=-1;LOCK_TIMEOUT=5000"})
class ReservationTests {
    @Autowired ReservationService service;
    @Autowired JdbcTemplate jdbc;
    @BeforeEach void reset() {
        jdbc.update("DELETE FROM outbox"); jdbc.update("DELETE FROM reservations");
        jdbc.update("UPDATE inventory SET available=5 WHERE sku='BOOK-1'");
    }
    int count(String table) { return jdbc.queryForObject("SELECT COUNT(*) FROM " + table, Integer.class); }
    int stock() { return jdbc.queryForObject("SELECT available FROM inventory WHERE sku='BOOK-1'", Integer.class); }
    @Test void commitsReservationStockAndEvent() {
        var result = service.reserve("buyer", new ReserveRequest("key-1", "BOOK-1", 2));
        assertEquals(3, stock()); assertEquals(1, count("reservations")); assertEquals(1, count("outbox"));
        assertEquals(result, service.get("buyer", result.id()));
    }
    @Test void shortageRollsBackInsertedReservation() {
        var error = assertThrows(BusinessException.class, () -> service.reserve("buyer", new ReserveRequest("key-1", "BOOK-1", 6)));
        assertEquals("OUT_OF_STOCK", error.code()); assertEquals(5, stock());
        assertEquals(0, count("reservations")); assertEquals(0, count("outbox"));
    }
    @Test void sameKeyReplaysWithoutSecondDecrease() {
        var request = new ReserveRequest("same", "BOOK-1", 2);
        assertEquals(service.reserve("buyer", request), service.reserve("buyer", request));
        assertEquals(3, stock()); assertEquals(1, count("outbox"));
    }
    @Test void sameKeyDifferentPayloadIsRejected() {
        service.reserve("buyer", new ReserveRequest("same", "BOOK-1", 1));
        assertEquals("IDEMPOTENCY_CONFLICT", assertThrows(BusinessException.class,
                () -> service.reserve("buyer", new ReserveRequest("same", "BOOK-1", 2))).code());
        assertEquals(4, stock());
    }
    @Test void otherOwnerCannotReadReservation() {
        var result = service.reserve("buyer", new ReserveRequest("same", "BOOK-1", 1));
        assertEquals("NOT_FOUND", assertThrows(BusinessException.class, () -> service.get("reader", result.id())).code());
    }
    @Test void negativeQuantityRejectedWithoutHttp() {
        assertThrows(BusinessException.class, () -> service.reserve("buyer", new ReserveRequest("bad", "BOOK-1", -1)));
        assertEquals(5, stock()); assertEquals(0, count("reservations"));
    }
    @Test void concurrentRequestsCannotOversell() throws Exception {
        var start = new CountDownLatch(1);
        try (var pool = Executors.newFixedThreadPool(12)) {
            var futures = new ArrayList<Future<Boolean>>();
            for (int i=0; i<12; i++) {
                final int number = i;
                futures.add(pool.submit(() -> {
                    start.await();
                    try { service.reserve("buyer", new ReserveRequest("parallel-" + number, "BOOK-1", 1)); return true; }
                    catch (BusinessException error) { assertEquals("OUT_OF_STOCK", error.code()); return false; }
                }));
            }
            start.countDown();
            int successes = 0;
            for (var future : futures) if (future.get(20, TimeUnit.SECONDS)) successes++;
            assertEquals(5, successes); assertEquals(0, stock());
            assertEquals(5, count("reservations")); assertEquals(5, count("outbox"));
        }
    }
}
