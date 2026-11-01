package com.example.reservation;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.beans.factory.annotation.Value;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = {"app.demo-password=test-only-password", "spring.datasource.url=jdbc:h2:mem:http;DB_CLOSE_DELAY=-1"})
class HttpTests {
    @Value("${local.server.port}") int port;
    URI uri(String path) { return URI.create("http://127.0.0.1:" + port + path); }
    String auth(String user) {
        return "Basic " + Base64.getEncoder().encodeToString((user + ":test-only-password").getBytes(StandardCharsets.UTF_8));
    }
    HttpClient client() { return HttpClient.newBuilder().cookieHandler(new CookieManager(null, CookiePolicy.ACCEPT_ALL)).build(); }
    String csrf(HttpClient client, String user) throws Exception {
        var response = client.send(HttpRequest.newBuilder(uri("/csrf")).header("Authorization", auth(user)).GET().build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(200, response.statusCode());
        var matcher = Pattern.compile("\"token\"\\s*:\\s*\"([^\"]+)\"").matcher(response.body());
        // JSON 문자열의 고정 필드만 읽는 테스트 보조 함수. 제품용 JSON 파서가 아니다.
        assertTrue(matcher.find(), response.body()); return matcher.group(1);
    }
    HttpResponse<String> post(HttpClient client, String user, String token, String body) throws Exception {
        var request = HttpRequest.newBuilder(uri("/api/reservations")).header("Authorization", auth(user))
                .header("Content-Type", "application/json").header("X-CSRF-TOKEN", token)
                .POST(HttpRequest.BodyPublishers.ofString(body)).build();
        return client.send(request, HttpResponse.BodyHandlers.ofString());
    }
    @Test void healthIsPublic() throws Exception {
        var response = client().send(HttpRequest.newBuilder(uri("/actuator/health")).GET().build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(200, response.statusCode()); assertTrue(response.body().contains("UP"));
    }
    @Test void anonymousReadIsUnauthorized() throws Exception {
        var response = client().send(HttpRequest.newBuilder(uri("/api/reservations/missing")).GET().build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(401, response.statusCode());
    }
    @Test void csrfRejectedBeforeBasicAuthentication() throws Exception {
        assertEquals(401, post(client(), "buyer", "missing", "{}").statusCode());
    }
    @Test void readerCannotReserve() throws Exception {
        var client = client();
        assertEquals(403, post(client, "reader", csrf(client, "reader"), "{\"requestKey\":\"role\",\"sku\":\"BOOK-1\",\"quantity\":1}").statusCode());
    }
    @Test void invalidQuantityIs400() throws Exception {
        var client = client();
        var response = post(client, "buyer", csrf(client, "buyer"), "{\"requestKey\":\"bad\",\"sku\":\"BOOK-1\",\"quantity\":0}");
        assertEquals(400, response.statusCode()); assertTrue(response.body().contains("INVALID_REQUEST"));
    }
    @Test void httpSuccessAndReplay() throws Exception {
        var client = client(); var token = csrf(client, "buyer");
        var body = "{\"requestKey\":\"http-ok\",\"sku\":\"BOOK-1\",\"quantity\":1}";
        var first = post(client, "buyer", token, body); var second = post(client, "buyer", token, body);
        assertEquals(200, first.statusCode()); assertEquals(first.body(), second.body());
    }
}
