package com.example.reservation;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;
@Repository
public class ReservationRepository {
    private final JdbcTemplate jdbc;
    private final RowMapper<Reservation> mapper = (rs, n) -> new Reservation(
            rs.getString("id"), rs.getString("owner_name"), rs.getString("request_key"),
            rs.getString("sku"), rs.getInt("quantity"));
    public ReservationRepository(JdbcTemplate jdbc) { this.jdbc = jdbc; }
    public Optional<Reservation> findByKey(String owner, String key) {
        return jdbc.query("SELECT * FROM reservations WHERE owner_name=? AND request_key=?",
                mapper, owner, key).stream().findFirst();
    }
    public Optional<Reservation> findById(String owner, String id) {
        return jdbc.query("SELECT * FROM reservations WHERE owner_name=? AND id=?",
                mapper, owner, id).stream().findFirst();
    }
    public boolean skuExists(String sku) {
        return jdbc.queryForObject("SELECT COUNT(*) FROM inventory WHERE sku=?", Integer.class, sku) > 0;
    }
    public void insert(Reservation value) {
        jdbc.update("INSERT INTO reservations(id, owner_name, request_key, sku, quantity) VALUES(?,?,?,?,?)",
                value.id(), value.owner(), value.requestKey(), value.sku(), value.quantity());
    }
    public boolean decrease(String sku, int quantity) {
        return jdbc.update("UPDATE inventory SET available=available-? WHERE sku=? AND available>=?",
                quantity, sku, quantity) == 1;
    }
    public void appendEvent(String reservationId) {
        jdbc.update("INSERT INTO outbox(event_id, reservation_id, event_type) VALUES(?,?,?)",
                UUID.randomUUID().toString(), reservationId, "ReservationCreated");
    }
}
