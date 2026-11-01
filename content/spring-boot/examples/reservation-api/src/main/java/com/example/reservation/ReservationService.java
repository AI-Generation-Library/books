package com.example.reservation;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
@Service
public class ReservationService {
    private final ReservationRepository repository;
    public ReservationService(ReservationRepository repository) { this.repository = repository; }
    @Transactional
    public Reservation reserve(String owner, ReserveRequest request) {
        // HTTP 이외의 호출에서도 도메인 제약을 지킨다.
        if (owner == null || owner.isBlank() || owner.length() > 80
                || request == null || request.requestKey() == null
                || !request.requestKey().matches("[A-Za-z0-9-]{1,80}")
                || request.sku() == null || request.sku().isBlank() || request.sku().length() > 40
                || request.quantity() < 1 || request.quantity() > 100) {
            throw new BusinessException("INVALID_COMMAND");
        }
        var existing = repository.findByKey(owner, request.requestKey());
        if (existing.isPresent()) {
            var previous = existing.get();
            if (!previous.sku().equals(request.sku()) || previous.quantity() != request.quantity()) {
                throw new BusinessException("IDEMPOTENCY_CONFLICT");
            }
            return previous;
        }
        if (!repository.skuExists(request.sku())) throw new BusinessException("SKU_NOT_FOUND");
        var value = new Reservation(UUID.randomUUID().toString(), owner,
                request.requestKey(), request.sku(), request.quantity());
        repository.insert(value);
        if (!repository.decrease(value.sku(), value.quantity())) throw new BusinessException("OUT_OF_STOCK");
        repository.appendEvent(value.id());
        return value;
    }
    @Transactional(readOnly = true)
    public Reservation get(String owner, String id) {
        return repository.findById(owner, id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
    }
}
