"""HTTP server with COOP/COEP for WebR/SharedArrayBuffer."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys
class H(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'cross-origin')
        super().end_headers()
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8788
HTTPServer(('', port), H).serve_forever()

import sys as _sys
if __name__ != "__main__":
    _sys.exit(0)

