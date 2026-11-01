package com.example.reservation;
public class BusinessException extends RuntimeException {
    private final String code;
    public BusinessException(String code) { super(code); this.code = code; }
    public String code() { return code; }
}
