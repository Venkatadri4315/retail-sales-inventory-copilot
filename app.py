import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from src import analytics
from src.orchestrator import handle_question


HOST = "0.0.0.0"
PORT = 8000

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


class RetailCopilotHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            self.serve_file(
                FRONTEND_DIR / "index.html",
                "text/html; charset=utf-8"
            )
            return

        if self.path == "/src/main.js":
            self.serve_file(
                FRONTEND_DIR / "src" / "main.js",
                "application/javascript; charset=utf-8"
            )
            return

        if self.path == "/src/style.css":
            self.serve_file(
                FRONTEND_DIR / "src" / "style.css",
                "text/css; charset=utf-8"
            )
            return

        if self.path == "/api/dashboard":
            self.handle_dashboard()
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path != "/api/ask":
            self.send_error(404, "Not Found")
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            if content_length <= 0:
                self.send_json(
                    400,
                    {"error": "Request body is empty."}
                )
                return

            body = self.rfile.read(content_length)

            try:
                payload = json.loads(
                    body.decode("utf-8")
                )
            except json.JSONDecodeError:
                self.send_json(
                    400,
                    {"error": "Invalid JSON request."}
                )
                return

            question = payload.get("question", "")

            if not isinstance(question, str) or not question.strip():
                self.send_json(
                    400,
                    {"error": "Question cannot be empty."}
                )
                return

            result = handle_question(
                question.strip()
            )

            self.send_json(200, result)

        except Exception as exc:
            print(f"API error: {exc}")

            self.send_json(
                500,
                {
                    "error": (
                        "The copilot could not process the request."
                    )
                }
            )

    def handle_dashboard(self):
        try:
            stockout_risks = analytics.get_stockout_risks(
                limit=1000
            )

            overstocked = analytics.get_overstock_items(
                limit=1000
            )

            non_moving = analytics.get_non_moving_items(
                limit=1000
            )

            sales_spikes = analytics.get_sales_spikes(
                limit=1000
            )

            sales_drops = analytics.get_sales_drops(
                limit=1000
            )

            dashboard_data = {
                "stockout_risks": len(stockout_risks),
                "overstocked": len(overstocked),
                "non_moving": len(non_moving),
                "sales_signals": (
                    len(sales_spikes) +
                    len(sales_drops)
                )
            }

            self.send_json(
                200,
                dashboard_data
            )

        except Exception as exc:
            print(f"Dashboard API error: {exc}")

            self.send_json(
                500,
                {
                    "error": (
                        "Unable to load dashboard metrics."
                    )
                }
            )

    def serve_file(self, file_path, content_type):
        if not file_path.exists():
            self.send_error(404, "File Not Found")
            return

        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header(
            "Content-Type",
            content_type
        )
        self.send_header(
            "Content-Length",
            str(len(content))
        )
        self.end_headers()

        self.wfile.write(content)

    def send_json(self, status_code, data):
        response = json.dumps(
            data,
            ensure_ascii=False,
            default=str
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()

        self.wfile.write(response)

    def log_message(self, format, *args):
        print(f"[HTTP] {format % args}")


def run_server():
    server = HTTPServer(
        (HOST, PORT),
        RetailCopilotHandler
    )

    print(
        f"Retail Sales & Inventory Copilot running at "
        f"http://localhost:{PORT}"
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopped.")

    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()