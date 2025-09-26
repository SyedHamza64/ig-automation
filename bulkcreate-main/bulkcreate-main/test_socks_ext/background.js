
chrome.proxy.settings.set({
    value: {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "socks5",
                host: "proxy.example.com",
                port: 1080
            }
        }
    },
    scope: "regular"
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

console.log("SOCKS5 proxy configured: proxy.example.com:1080");
