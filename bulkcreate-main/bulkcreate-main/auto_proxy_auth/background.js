chrome.webRequest.onAuthRequired.addListener(
  function(details) {
    return {
      authCredentials: {
        username: "PROXY_USERNAME",
        password: "PROXY_PASSWORD"
      }
    };
  },
  {urls: ["<all_urls>"]},
  ["blocking"]
);