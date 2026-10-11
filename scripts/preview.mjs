import http from "node:http"
import handler from "serve-handler"

const port = Number(process.env.PORT || 8080)
const basePath = process.env.BASE_PATH ? `/${process.env.BASE_PATH.replace(/^\/+|\/+$/g, "")}/` : "/"
const server = http.createServer((request, response) => {
  if (basePath !== "/") {
    if (request.url === "/" || request.url === basePath.slice(0, -1)) {
      response.writeHead(302, { Location: basePath })
      return response.end()
    }
    if (!request.url?.startsWith(basePath)) {
      response.writeHead(404)
      return response.end("Not found")
    }
    request.url = "/" + request.url.slice(basePath.length)
  }
  return handler(request, response, { public: "dist", cleanUrls: true, directoryListing: false })
})
server.listen(port, "127.0.0.1", () => {
  console.log(`Local: http://127.0.0.1:${port}${basePath}`)
})
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.close(() => process.exit(0)))
}
