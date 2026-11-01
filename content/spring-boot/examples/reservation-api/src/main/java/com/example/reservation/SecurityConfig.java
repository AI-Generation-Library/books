package com.example.reservation;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
@Configuration(proxyBeanMethods = false)
public class SecurityConfig {
    @Bean
    InMemoryUserDetailsManager users(@Value("${app.demo-password}") String password) {
        if (password.isBlank()) throw new IllegalArgumentException("APP_DEMO_PASSWORD must not be blank");
        var encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder();
        return new InMemoryUserDetailsManager(
                User.withUsername("buyer").password(encoder.encode(password)).roles("BUYER").build(),
                User.withUsername("reader").password(encoder.encode(password)).roles("READER").build());
    }
    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        return http.authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers(HttpMethod.POST, "/api/reservations").hasRole("BUYER")
                .anyRequest().authenticated())
                .httpBasic(Customizer.withDefaults())
                .csrf(Customizer.withDefaults())
                .build();
    }
}
