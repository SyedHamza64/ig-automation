# WebProxy Browser Profile Manager

A powerful browser profile management system that allows you to create, manage, and launch isolated browser sessions with unique fingerprints and proxy configurations.

## 🚀 Features

- **Isolated Browser Profiles**: Each profile maintains separate cookies, cache, and browsing data
- **Proxy Support**: Configure different proxies for each profile
- **Fingerprint Randomization**: Random user agents, screen resolutions, languages, and timezones
- **Session Management**: Real-time tracking of active/inactive profiles
- **Groups & Analytics**: Organize profiles and monitor usage statistics
- **Modern UI**: Clean, responsive React-based dashboard

## 📋 Prerequisites

- **Node.js** (v16 or higher) - [Download here](https://nodejs.org)
- **Python** (v3.7 or higher) - [Download here](https://python.org)
- **Chrome Browser** installed on your system

## ⚙️ Installation

### 1. Install Python Dependencies
```bash
pip install undetected-chromedriver selenium
pip install setuptools
```

### (Optional: Fix Windows Restrictions)
```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted
```

### 2. Setup Backend Server (user powershell not cmd)
```bash
cd server
npm install
```

### 3. Setup Frontend Client
```bash
cd client
npm install
```

### 4. Configure ChromeDriver Path
Edit `manager.py` and update line 12 with your system path:
```python
CHROMEDRIVER_PATH = "C:/path/to/your/webProxy/chromedriver.exe"
```

## 🚀 Running the Application

### Start Backend Server (Terminal 1):
```bash
cd server
npm run dev
```
*Server runs on http://localhost:4000*

### Start Frontend Client (Terminal 2):
```bash
cd client
npm run dev
```
*Client runs on http://localhost:5173*

## 📖 Usage

### Creating Profiles
1. Click "Create Profile" button
2. Enter profile name
3. Configure proxy (optional): `http://username:password@host:port`
4. Set browser preferences (user agent, window size, etc.)
5. Click "Create"

### Managing Profiles
- **Launch**: Start browser with selected profile
- **Close**: Terminate active browser session
- **View Details**: See profile configuration
- **Delete**: Remove profile and its data

### Proxy Configuration
Supported formats:
- HTTP: `http://host:port`
- HTTP with auth: `http://username:password@host:port`
- SOCKS5: `socks5://host:port`

## 📁 Project Structure

```
webProxy/
├── client/                 # React frontend
│   ├── src/
│   ├── components/
│   └── package.json
├── server/                 # Node.js backend
│   ├── data/              # JSON data storage
│   ├── server.js
│   └── package.json
├── selenium_profiles/      # Profile data storage
├── manager.py             # Python automation script
├── chromedriver.exe       # Chrome WebDriver
└── README.md
```

## 🔧 API Endpoints

- `GET /api/profiles` - List all profiles
- `POST /api/profiles` - Create new profile
- `POST /api/profiles/launch` - Launch profile
- `POST /api/profiles/close` - Close profile
- `POST /api/profiles/delete` - Delete profile
- `GET /api/status` - Get running profiles
- `GET /api/groups` - Manage profile groups
- `GET /api/proxies` - Manage proxy configurations

## 🛠️ Troubleshooting

### Common Issues

**Profiles won't launch:**
- Check ChromeDriver path in `manager.py`
- Ensure Chrome browser is installed
- Verify Python dependencies are installed

**Connection errors:**
- Ensure both servers are running
- Check if ports 4000 and 5173 are available
- Verify firewall settings

**Proxy issues:**
- Verify proxy format and credentials
- Test proxy connection separately
- Check proxy server availability

### Debug Mode
Check browser console (F12) for detailed error messages.

## 💡 Tips

- Each profile creates a separate Chrome user data directory
- Profiles persist between application restarts
- Use different proxies for better anonymity
- Monitor active sessions in the dashboard
- Regular cleanup of unused profiles recommended

## 🔒 Security Notes

- Profile data is stored locally in `selenium_profiles/`
- Proxy credentials are stored in plain text
- Each profile runs in isolated Chrome instance
- No data is shared between profiles


## 🤝 Support

For issues or questions, check the troubleshooting section or review the console logs for detailed error information.
