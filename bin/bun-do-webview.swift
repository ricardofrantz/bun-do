import Cocoa
import WebKit

let port = ProcessInfo.processInfo.environment["BUNDO_PORT"] ?? "8000"
let url = URL(string: "http://127.0.0.1:\(port)/")!

let app = NSApplication.shared
app.setActivationPolicy(.regular)

let window = NSWindow(
    contentRect: NSRect(x: 0, y: 0, width: 1024, height: 768),
    styleMask: [.titled, .closable, .resizable, .miniaturizable],
    backing: .buffered,
    defer: false
)
window.title = "bun-do"
window.center()

let webView = WKWebView(frame: window.contentView!.bounds)
webView.autoresizingMask = [.width, .height]
window.contentView!.addSubview(webView)
webView.load(URLRequest(url: url))

window.makeKeyAndOrderFront(nil)
app.activate(ignoringOtherApps: true)

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}
let delegate = AppDelegate()
app.delegate = delegate
app.run()
