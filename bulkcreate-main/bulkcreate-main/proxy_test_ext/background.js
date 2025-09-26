
chrome.proxy.settings.set({
    value: {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "socks5",
                host: "proxy.example.com",
                port: 1080
            },
            bypassList: []
        }
    },
    scope: "regular"
}, function() {
    console.log("Proxy set to SOCKS5 proxy.example.com:1080");
});

chrome.webRequest.onAuthRequired.addListener(
    function(details) {
        console.log("Auth required for:", details.url);
        return {
            authCredentials: {
                username: "testuser",
                password: "testpass"
            }
        };
    },
    {urls: ["<all_urls>"]},
    ["blocking"]
);

// Force proxy usage - block direct connections
chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
        console.log("Request:", details.url);
        return {};
    },
    {urls: ["<all_urls>"]},
    ["blocking"]
);
