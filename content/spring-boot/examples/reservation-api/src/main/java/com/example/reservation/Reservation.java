package com.example.reservation;
public record Reservation(String id, String owner, String requestKey, String sku, int quantity) {}
