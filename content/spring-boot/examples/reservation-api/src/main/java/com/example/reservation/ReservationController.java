package com.example.reservation;
import java.security.Principal;
import java.util.Map;
import jakarta.validation.Valid;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.*;
@RestController
public class ReservationController {
    private final ReservationService service;
    public ReservationController(ReservationService service) { this.service = service; }
    @PostMapping("/api/reservations")
    public Reservation reserve(Principal principal, @Valid @RequestBody ReserveRequest request) {
        // 최초 생성과 동일 키 재조회 모두 200으로 정의한 예약 명령 API.
        return service.reserve(principal.getName(), request);
    }
    @GetMapping("/api/reservations/{id}")
    public Reservation get(Principal principal, @PathVariable String id) {
        return service.get(principal.getName(), id);
    }
    @GetMapping("/csrf")
    public Map<String, String> csrf(CsrfToken token) {
        return Map.of("headerName", token.getHeaderName(), "token", token.getToken());
    }
}
