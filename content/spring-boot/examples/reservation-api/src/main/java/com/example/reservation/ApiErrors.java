package com.example.reservation;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
@RestControllerAdvice
public class ApiErrors {
    private ProblemDetail problem(HttpStatus status, String code, String detail) {
        var result = ProblemDetail.forStatusAndDetail(status, detail);
        result.setProperty("code", code);
        return result;
    }
    @ExceptionHandler(BusinessException.class)
    ProblemDetail business(BusinessException error) {
        var status = switch (error.code()) {
            case "NOT_FOUND", "SKU_NOT_FOUND" -> HttpStatus.NOT_FOUND;
            case "INVALID_COMMAND" -> HttpStatus.BAD_REQUEST;
            default -> HttpStatus.CONFLICT;
        };
        return problem(status, error.code(), "요청 조건을 확인하세요.");
    }
    @ExceptionHandler({MethodArgumentNotValidException.class, HttpMessageNotReadableException.class})
    ProblemDetail invalid(Exception error) {
        return problem(HttpStatus.BAD_REQUEST, "INVALID_REQUEST", "요청 본문을 확인하세요.");
    }
    @ExceptionHandler(DuplicateKeyException.class)
    ProblemDetail duplicate(DuplicateKeyException error) {
        return problem(HttpStatus.CONFLICT, "DUPLICATE_REQUEST", "동시 요청이 처리 중일 수 있습니다. 같은 키와 본문으로 다시 확인하세요.");
    }
}
