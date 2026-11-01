package com.example.reservation;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.*;
import static org.junit.jupiter.api.Assertions.*;
class DiTests {
    interface FeePolicy { int fee(int price); }
    record Checkout(FeePolicy policy) { int total(int price) { return price + policy.fee(price); } }
    @Test void constructorInjectionNeedsNoContainer() {
        var checkout = new Checkout(price -> 0);
        assertEquals(1000, checkout.total(1000));
    }
    @Configuration(proxyBeanMethods = false)
    static class Config {
        @Bean FeePolicy policy() { return price -> 100; }
        @Bean Checkout checkout(FeePolicy policy) { return new Checkout(policy); }
    }
    @Test void containerAssemblesAndReusesSingleton() {
        try (var context = new AnnotationConfigApplicationContext(Config.class)) {
            assertEquals(1100, context.getBean(Checkout.class).total(1000));
            assertSame(context.getBean(Checkout.class), context.getBean(Checkout.class));
        }
    }
}
