package com.example.reservation;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
public record ReserveRequest(
        @NotBlank @Size(max = 80) @Pattern(regexp = "[A-Za-z0-9-]+") String requestKey,
        @NotBlank @Size(max = 40) String sku,
        @Min(1) @Max(100) int quantity) {}
