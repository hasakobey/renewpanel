import http.server, sys, functools
h = http.server.SimpleHTTPRequestHandler
h.extensions_map.update({'.css':'text/css', '.js':'text/javascript'})
handler = functools.partial(h, directory=sys.argv[2])
http.server.HTTPServer(('127.0.0.1', int(sys.argv[1])), handler).serve_forever()
