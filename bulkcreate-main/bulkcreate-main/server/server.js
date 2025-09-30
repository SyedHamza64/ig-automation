// backend/server.js
const express = require('express');
// Global error logging to prevent silent exits
process.on('uncaughtException', (err) => {
  console.error('[uncaughtException]', err && err.stack ? err.stack : err);
});
process.on('unhandledRejection', (reason) => {
  console.error('[unhandledRejection]', reason);
});
const { spawn } = require('child_process');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const multer = require('multer');
const app = express();
const PORT = 4000;

const runningProcesses = new Map();

// Data storage files
const DATA_DIR = './data';
const GROUPS_FILE = path.join(DATA_DIR, 'groups.json');
const PROXIES_FILE = path.join(DATA_DIR, 'proxies.json');
const SETTINGS_FILE = path.join(DATA_DIR, 'settings.json');
const ANALYTICS_FILE = path.join(DATA_DIR, 'analytics.json');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR);
}

// Helper functions
const readJsonFile = (filePath, defaultData = []) => {
    try {
        if (fs.existsSync(filePath)) {
            return JSON.parse(fs.readFileSync(filePath, 'utf8'));
        }
    } catch (error) {
        console.error(`Error reading ${filePath}:`, error);
    }
    return defaultData;
};

const writeJsonFile = (filePath, data) => {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        return true;
    } catch (error) {
        console.error(`Error writing ${filePath}:`, error);
        return false;
    }
};

// Initialize default data
if (!fs.existsSync(GROUPS_FILE)) {
    writeJsonFile(GROUPS_FILE, []);
}
if (!fs.existsSync(PROXIES_FILE)) {
    writeJsonFile(PROXIES_FILE, []);
}
if (!fs.existsSync(SETTINGS_FILE)) {
    writeJsonFile(SETTINGS_FILE, {
        notifications: true,
        autoStart: false,
        darkMode: true,
        language: 'en',
        defaultProxy: '',
        maxProfiles: 50,
        sessionTimeout: 30,
        autoBackup: true,
        backupInterval: 24
    });
}
if (!fs.existsSync(ANALYTICS_FILE)) {
    writeJsonFile(ANALYTICS_FILE, {
        sessions: [],
        stats: { totalSessions: 0, activeProfiles: 0, avgSessionTime: 0, countries: 0 }
    });
}

app.use(cors());
app.use(express.json());

// API to get the list of profiles
app.get('/api/profiles', (req, res) => {
    console.log('=== API /api/profiles called - UPDATED CODE ===');
    const pythonProcess = spawn('python', ['manager.py', 'list'], {
        cwd: path.join(__dirname, '..')
    });

    let profileData = '';
    pythonProcess.stdout.on('data', (data) => {
        profileData += data.toString();
    });

    pythonProcess.on('close', () => {
         try {
            const profiles = JSON.parse(profileData);
            console.log(`Processing ${Object.keys(profiles).length} profiles from manager.py`);
            
            // Add enhanced mode information to each profile
            const profilesWithEnhanced = {};
            for (const [name, config] of Object.entries(profiles)) {
                // Check if profile has enhanced mode flag and anti-detection features
                const enhancedModePath = path.join(__dirname, '../selenium_profiles', name, 'enhanced_mode.json');
                let enhancedMode = false;
                let antiDetection = {};
                
                // Debug: Log every profile being processed
                console.log(`Processing profile: ${name}`);
                
                try {
                    if (fs.existsSync(enhancedModePath)) {
                        const metadata = JSON.parse(fs.readFileSync(enhancedModePath, 'utf8'));
                        enhancedMode = metadata.enhancedMode || false;
                        antiDetection = metadata.anti_detection || {};
                        
                        // Debug logging for all profiles
                        if (name === 'test_features_profile') {
                            console.log(`DEBUG - Reading enhanced_mode.json for ${name}:`, {
                                enhancedModePath,
                                metadata,
                                enhancedMode,
                                antiDetection
                            });
                        }
                    } else {
                        // Debug logging for missing files
                        if (name === 'test_features_profile') {
                            console.log(`DEBUG - Enhanced mode file not found for ${name}:`, enhancedModePath);
                        }
                    }
                } catch (error) {
                    console.warn(`Could not read enhanced mode for ${name}:`, error.message);
                    if (name === 'test_features_profile') {
                        console.log(`DEBUG - Error reading enhanced_mode.json for ${name}:`, error);
                    }
                }
                
                profilesWithEnhanced[name] = {
                    ...config,
                    enhancedMode: enhancedMode,
                    anti_detection: antiDetection
                };
                
                // Debug: Log the final profile data
                if (name === 'test_features_profile') {
                    console.log(`FINAL PROFILE DATA for ${name}:`, profilesWithEnhanced[name]);
                }
                
                // Debug logging for test profile
                if (name === 'test_features_profile') {
                    console.log(`DEBUG - Profile ${name}:`, {
                        enhancedMode,
                        anti_detection: antiDetection,
                        enhancedModePath
                    });
                }
            }
            
            console.log(`Returning ${Object.keys(profilesWithEnhanced).length} profiles to UI`);
            res.json(profilesWithEnhanced);
        } catch (e) {
            console.error('Error processing profiles:', e);
            res.status(500).json({ error: "Failed to parse profile data.", details: e.message });
        }
    });
});

// API to create a new profile
app.post('/api/profiles', (req, res) => {
    const { name, config, enhancedMode = false, antiDetection = {} } = req.body;
    
    console.log('Create profile request:', { name, enhancedMode, antiDetection });
    
    // If enhanced mode is enabled, use our enhanced creation method
    if (enhancedMode) {
        // Add anti-detection config to the profile config
        const enhancedConfig = {
            ...config,
            anti_detection: antiDetection
        };
        return createEnhancedProfile(name, enhancedConfig, res);
    }
    
    // Default bulkcreate-main method (standard mode)
    const args = ['manager.py', 'create', '--name', name];
    
    // Handle proxy from config or direct proxy field (backward compatibility)
    const proxy = config?.proxy || req.body.proxy;
    if (proxy && proxy.trim()) {
        args.push('--proxy', proxy.trim());
    }
    
    // Add config as JSON string if provided (without enhanced_mode flag)
    if (config) {
        const standardConfig = { ...config };
        delete standardConfig.enhanced_mode; // Remove enhanced_mode flag for standard profiles
        args.push('--config', JSON.stringify(standardConfig));
    }

    const pythonProcess = spawn('python', args, {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(201).json({ message: `Profile '${name}' created.` });
        } else {
            console.error('Create profile error:', errorOutput);
            
            // Check for specific error messages
            if (errorOutput.includes('already exists')) {
                res.status(400).json({ 
                    error: `Profile '${name}' already exists. Please use a different name.`,
                    details: errorOutput 
                });
            } else {
                res.status(500).json({ error: 'Failed to create profile', details: errorOutput });
            }
        }
    });
});

// Enhanced profile creation function
function createEnhancedProfile(name, config, res) {
    const path = require('path');
    const enhancedScript = path.join(__dirname, '../bulkcreate_enhanced_test.py');
    
    // Create a temporary config for the enhanced script with anti-detection features
    const enhancedConfig = {
        ...config,
        enhanced_mode: true,  // This tells the script it's an enhanced mode profile
        profile_name: name,
        anti_detection: config.anti_detection || {}  // Include anti-detection configuration
    };
    
    console.log(`Creating enhanced profile '${name}' with anti-detection config:`, enhancedConfig.anti_detection);
    
    const args = ['python', enhancedScript, '--create-only', '--name', name, '--config', JSON.stringify(enhancedConfig)];
    
    const pythonProcess = spawn(args[0], args.slice(1), {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(201).json({ message: `Enhanced profile '${name}' created successfully.` });
        } else {
            console.error('Enhanced create profile error:', errorOutput);
            
            // Check for specific error messages
            if (errorOutput.includes('already exists as ENHANCED profile')) {
                res.status(400).json({ 
                    error: `Profile '${name}' already exists as an Enhanced profile. Please use a different name for your Standard profile.`,
                    details: errorOutput 
                });
            } else if (errorOutput.includes('already exists as STANDARD profile')) {
                res.status(400).json({ 
                    error: `Profile '${name}' already exists as a Standard profile. Please use a different name for your Enhanced profile.`,
                    details: errorOutput 
                });
            } else if (errorOutput.includes('already exists')) {
                res.status(400).json({ 
                    error: `Profile '${name}' already exists. Please use a different name.`,
                    details: errorOutput 
                });
            } else {
                res.status(500).json({ error: 'Failed to create enhanced profile', details: errorOutput });
            }
        }
    });
}

// Helper function to find next available profile numbers
function findNextAvailableNumbers(prefix, suffix, count) {
    const fs = require('fs');
    const path = require('path');
    const profilesPath = path.join(__dirname, '../selenium_profiles');
    const profilesFile = path.join(profilesPath, 'profiles.json');
    
    let existingProfiles = {};
    try {
        if (fs.existsSync(profilesFile)) {
            const profilesData = fs.readFileSync(profilesFile, 'utf8');
            existingProfiles = JSON.parse(profilesData);
        }
    } catch (error) {
        console.warn('Could not read profiles.json:', error.message);
    }
    
    const availableNumbers = [];
    let currentNumber = 1;
    
    while (availableNumbers.length < count) {
        const profileName = prefix ? `${prefix}_${suffix}_${currentNumber}` : `${suffix}_profile_${currentNumber}`;
        
        if (!existingProfiles[profileName]) {
            availableNumbers.push(currentNumber);
        }
        currentNumber++;
    }
    
    return availableNumbers;
}

// Enhanced bulk profile creation function (sequential like standard bulk creation)
function createBulkEnhancedProfiles(count, deviceType, prefix, antiDetectionConfig, res) {
    const path = require('path');
    const enhancedScript = path.join(__dirname, '../bulkcreate_enhanced_test.py');
    
    // Find next available numbers to avoid conflicts
    const availableNumbers = findNextAvailableNumbers(prefix, 'enh', count);
    
    let createdProfiles = [];
    let failedProfiles = [];
    let currentIndex = 0;
    
    function createNextProfile() {
        if (currentIndex >= count) {
            // All profiles processed
            if (failedProfiles.length === 0) {
                res.status(201).json({ 
                    message: `Created ${createdProfiles.length} enhanced profiles successfully.`,
                    details: createdProfiles
                });
            } else {
                res.status(207).json({ // 207 Multi-Status
                    message: `Created ${createdProfiles.length} profiles, ${failedProfiles.length} failed.`,
                    successful: createdProfiles.length,
                    failed: failedProfiles.length,
                    created: createdProfiles,
                    errors: failedProfiles
                });
            }
            return;
        }
        
        currentIndex++;
        const profileNumber = availableNumbers[currentIndex - 1];
        const profileName = prefix ? `${prefix}_enh_${profileNumber}` : `enhanced_profile_${profileNumber}`;
        
        // Create a config for each profile with anti-detection settings
        const enhancedConfig = {
            enhanced_mode: true,
            profile_name: profileName,
            user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            language: "en-US,en;q=0.9",
            timezone: "Europe/Berlin",
            webrtc: "disabled",
            window_size: [1920, 1080],
            startup_urls: [],
            remark: `Enhanced profile ${currentIndex} created via bulk operation`,
            deviceType: deviceType,
            anti_detection: antiDetectionConfig || {}  // Include anti-detection configuration
        };
        
        // Add device type specific settings (same as standard bulk creation)
        if (deviceType === 'ios') {
            enhancedConfig.window_size = [375, 667]; // iPhone size
            enhancedConfig.user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1";
        } else if (deviceType === 'android') {
            enhancedConfig.window_size = [360, 640]; // Android size
            enhancedConfig.user_agent = "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36";
        } else if (deviceType === 'windows') {
            enhancedConfig.window_size = [1920, 1080];
            enhancedConfig.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
        } else if (deviceType === 'macos') {
            enhancedConfig.window_size = [1920, 1080];
            enhancedConfig.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
        }
        
        const args = ['python', enhancedScript, '--create-only', '--name', profileName, '--config', JSON.stringify(enhancedConfig)];
        
        const pythonProcess = spawn(args[0], args.slice(1));
        
        let errorOutput = '';
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                createdProfiles.push(profileName);
                console.log(`✅ Created enhanced profile: ${profileName}`);
            } else {
                // Check if it's just a conflict (profile already exists)
                if (errorOutput.includes('already exists')) {
                    console.log(`⚠️ Profile '${profileName}' already exists. Skipping.`);
                    // Don't count as failed, just skip
                } else {
                    failedProfiles.push({ name: profileName, error: errorOutput });
                    console.error(`❌ Failed to create enhanced profile '${profileName}':`, errorOutput);
                }
            }
            
            // Continue with next profile
            setTimeout(createNextProfile, 100); // Small delay between creations
        });
    }
    
    // Start creating profiles sequentially
    createNextProfile();
}

// API to launch a profile
app.get('/api/status', (req, res) => {
    res.json(Array.from(runningProcesses.keys()));
});

// UPDATED /launch endpoint to track the process
app.post('/api/profiles/launch', (req, res) => {
    const { name } = req.body;

    if (runningProcesses.has(name)) {
        return res.status(400).json({ error: `Profile '${name}' is already running.` });
    }

    // Check if profile was created with enhanced mode
    const path = require('path');
    const fs = require('fs');
    const profileMetadataPath = path.join(__dirname, '../selenium_profiles', name, 'enhanced_mode.json');
    
    let enhancedMode = false;
    try {
        if (fs.existsSync(profileMetadataPath)) {
            const metadata = JSON.parse(fs.readFileSync(profileMetadataPath, 'utf8'));
            enhancedMode = metadata.enhancedMode || false;
        }
    } catch (error) {
        console.warn(`Could not read enhanced mode metadata for ${name}:`, error.message);
    }

    // If enhanced mode is enabled, use our enhanced launch method
    if (enhancedMode) {
        return launchEnhancedProfile(name, res);
    }

    // Default bulkcreate-main launch method
    const pythonProcess = spawn('python', ['manager.py', 'launch', '--name', name], {
        cwd: path.join(__dirname, '..')
    });
    
    // Store the process PID by profile name
    runningProcesses.set(name, pythonProcess);
    console.log(`[+] Process started for '${name}' with PID: ${pythonProcess.pid}`);

    // Pipe logs for visibility
    pythonProcess.stdout.on('data', (d) => {
        const txt = d.toString();
        console.log(`[mgr:${name}] ${txt.trim()}`);
    });
    pythonProcess.stderr.on('data', (d) => {
        const txt = d.toString();
        console.warn(`[mgr:${name}:err] ${txt.trim()}`);
    });

    // When the process closes (e.g., user closes the browser), remove it from our list
    pythonProcess.on('close', (code) => {
        runningProcesses.delete(name);
        console.log(`[-] Process for '${name}' closed with code ${code}.`);
    });

    res.status(200).json({ message: `Launch command issued for '${name}'.` });
});

// Cache for last known DevTools WS per profile
const lastKnownWs = new Map();

// New: launch and return DevTools WS for CDP control
app.post('/api/profiles/launch-cdp', (req, res) => {
    const { name } = req.body;

    if (!name) return res.status(400).json({ error: 'name required' });
    if (runningProcesses.has(name)) {
        // If already running, try to return existing WS immediately
        if (lastKnownWs.has(name)) {
            return res.status(200).json({ ws: lastKnownWs.get(name), from: 'cache' });
        }
        // Attempt to resolve via DevToolsActivePort
        const devtoolsFile = path.join(__dirname, '../selenium_profiles', name, 'DevToolsActivePort');
        try {
            if (fs.existsSync(devtoolsFile)) {
                const content = fs.readFileSync(devtoolsFile, 'utf8').trim();
                const port = parseInt(content.split(/\r?\n/)[0], 10);
                if (port > 0) {
                    const http = require('http');
                    const opts = { hostname: '127.0.0.1', port, path: '/json/version', method: 'GET' };
                    const req2 = http.request(opts, (r2) => {
                        let data = '';
                        r2.on('data', (c) => (data += c.toString()));
                        r2.on('end', () => {
                            try {
                                const meta = JSON.parse(data);
                                const ws = meta.webSocketDebuggerUrl;
                                if (ws) {
                                    lastKnownWs.set(name, ws);
                                    return res.status(200).json({ ws, from: 'probe' });
                                }
                            } catch {}
                            return res.status(409).json({ error: `Profile '${name}' is already running.` });
                        });
                    });
                    req2.on('error', () => res.status(409).json({ error: `Profile '${name}' is already running.` }));
                    req2.end();
                    return;
                }
            }
        } catch {}
        return res.status(409).json({ error: `Profile '${name}' is already running.` });
    }

    // Detect if enhanced
    const profileMetadataPath = path.join(__dirname, '../selenium_profiles', name, 'enhanced_mode.json');
    let enhancedMode = false;
    try {
        if (fs.existsSync(profileMetadataPath)) {
            const metadata = JSON.parse(fs.readFileSync(profileMetadataPath, 'utf8'));
            enhancedMode = metadata.enhancedMode || false;
        }
    } catch (e) {}

    const spawnArgs = enhancedMode
        ? ['python', path.join(__dirname, '../bulkcreate_enhanced_test.py'), '--launch-only', '--name', name]
        : ['python', 'manager.py', 'launch', '--name', name];

    const env = { ...process.env, REMOTE_DEBUG: 'true' };
    const proc = spawn(spawnArgs[0], spawnArgs.slice(1), { cwd: path.join(__dirname, '..'), env });
    runningProcesses.set(name, proc);

    let wsLine = '';
    let resolved = false;
    const profileDevtoolsFile = path.join(__dirname, '../selenium_profiles', name, 'DevToolsActivePort');

    const onData = (data) => {
        if (resolved) return;
        const text = data.toString();
        // look for a single-line JSON {"ws":"..."}
        const match = text.match(/\{\"ws\"\s*:\s*\"[^\"]+\"\}/);
        if (match) {
            wsLine = match[0];
            try {
                const parsed = JSON.parse(wsLine);
                resolved = true;
                if (parsed.ws) {
                    lastKnownWs.set(name, parsed.ws);
                }
                res.status(200).json(parsed);
            } catch (e) {
                // ignore parse error
            }
        }
    };

    proc.stdout.on('data', (d) => {
        const txt = d.toString();
        console.log(`[cdp:${name}] ${txt.trim()}`);
        onData(d);
    });
    proc.stderr.on('data', (d) => {
        const txt = d.toString();
        console.warn(`[cdp:${name}:err] ${txt.trim()}`);
    });

    // Fallback: poll DevToolsActivePort and derive WS URL
    let tries = 0;
    const maxTries = 20; // ~10s
    const tryResolveFromFile = () => {
        if (resolved) return;
        tries += 1;
        try {
            if (fs.existsSync(profileDevtoolsFile)) {
                const content = fs.readFileSync(profileDevtoolsFile, 'utf8').trim();
                const port = parseInt(content.split(/\r?\n/)[0], 10);
                if (port > 0) {
                    // Query /json/version to get webSocketDebuggerUrl
                    const http = require('http');
                    const opts = { hostname: '127.0.0.1', port, path: '/json/version', method: 'GET' };
                    const req2 = http.request(opts, (r2) => {
                        let data = '';
                        r2.on('data', (c) => (data += c.toString()));
                        r2.on('end', () => {
                            try {
                                const meta = JSON.parse(data);
                                const ws = meta.webSocketDebuggerUrl;
                                if (ws && !resolved) {
                                    resolved = true;
                                    lastKnownWs.set(name, ws);
                                    return res.status(200).json({ ws });
                                }
                            } catch {}
                            if (!resolved && tries < maxTries) setTimeout(tryResolveFromFile, 500);
                        });
                    });
                    req2.on('error', () => {
                        if (!resolved && tries < maxTries) setTimeout(tryResolveFromFile, 500);
                    });
                    req2.end();
                    return;
                }
            }
        } catch {}
        if (!resolved && tries < maxTries) setTimeout(tryResolveFromFile, 500);
    };
    setTimeout(tryResolveFromFile, 400);

    proc.on('close', (code) => {
        runningProcesses.delete(name);
        if (!resolved) {
            res.status(500).json({ error: 'launch ended without WS', code });
        }
    });
});

// Enhanced profile launch function
function launchEnhancedProfile(name, res) {
    const path = require('path');
    const enhancedScript = path.join(__dirname, '../bulkcreate_enhanced_test.py');
    
    const args = ['python', enhancedScript, '--launch-only', '--name', name];
    
    const pythonProcess = spawn(args[0], args.slice(1));
    
    // Store the process PID by profile name
    runningProcesses.set(name, pythonProcess);
    console.log(`[+] Enhanced process started for '${name}' with PID: ${pythonProcess.pid}`);

    // Pipe logs for visibility
    pythonProcess.stdout.on('data', (d) => {
        const txt = d.toString();
        console.log(`[enh:${name}] ${txt.trim()}`);
    });
    pythonProcess.stderr.on('data', (d) => {
        const txt = d.toString();
        console.warn(`[enh:${name}:err] ${txt.trim()}`);
    });

    // When the process closes (e.g., user closes the browser), remove it from our list
    pythonProcess.on('close', (code) => {
        runningProcesses.delete(name);
        console.log(`[-] Enhanced process for '${name}' closed with code ${code}.`);
    });

    res.status(200).json({ message: `Enhanced launch command issued for '${name}'.` });
}

// NEW /close endpoint to terminate a process
app.post('/api/profiles/close', (req, res) => {
    const { name } = req.body;

    if (runningProcesses.has(name)) {
        const processToKill = runningProcesses.get(name);
        const pid = processToKill.pid;
        
        // Force kill the process tree on Windows
        try {
            // Use taskkill to force kill the process tree
            spawn('taskkill', ['/pid', pid.toString(), '/t', '/f'], { stdio: 'ignore' });
            console.log(`Force killed process tree for PID: ${pid}`);
        } catch (error) {
            console.error('Error killing process:', error);
            // Fallback to regular kill
            try {
                processToKill.kill('SIGKILL');
            } catch (e) {
                console.error('Fallback kill also failed:', e);
            }
        }
        
        runningProcesses.delete(name);
        res.status(200).json({ message: `Close command issued for '${name}'.` });
    } else {
        res.status(404).json({ error: `No running process found for profile '${name}'.` });
    }
});

// API to delete a profile
app.post('/api/profiles/delete', (req, res) => {
    const { name } = req.body;
    const pythonProcess = spawn('python', ['manager.py', 'delete', '--name', name], {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(200).json({ message: `Profile '${name}' deleted.` });
        } else {
            console.error('Delete profile error:', errorOutput);
            res.status(500).json({ error: 'Failed to delete profile', details: errorOutput });
        }
    });
});

// API for bulk profile creation
app.post('/api/profiles/bulk-create', (req, res) => {
    const { count, deviceType, prefix, enhancedMode = false, antiDetection = {} } = req.body;
    
    console.log('Bulk create request:', { count, deviceType, prefix, enhancedMode, antiDetection });
    
    // If enhanced mode is enabled, use our enhanced bulk creation method
    if (enhancedMode) {
        return createBulkEnhancedProfiles(count, deviceType, prefix, antiDetection, res);
    }
    
    // Default bulkcreate-main method (standard mode)
    // Find next available numbers to avoid conflicts
    const availableNumbers = findNextAvailableNumbers(prefix, 'std', count);
    
    // For standard mode, we'll create profiles individually with custom names
    // since manager.py bulk-create doesn't support custom numbering
    let createdProfiles = [];
    let failedProfiles = [];
    let currentIndex = 0;
    
    function createNextStandardProfile() {
        if (currentIndex >= count) {
            // All profiles processed
            if (failedProfiles.length === 0) {
                res.status(201).json({ 
                    message: `Created ${createdProfiles.length} standard profiles successfully.`,
                    details: createdProfiles
                });
            } else {
                res.status(207).json({ // 207 Multi-Status
                    message: `Created ${createdProfiles.length} profiles, ${failedProfiles.length} failed.`,
                    successful: createdProfiles.length,
                    failed: failedProfiles.length,
                    created: createdProfiles,
                    errors: failedProfiles
                });
            }
            return;
        }
        
        currentIndex++;
        const profileNumber = availableNumbers[currentIndex - 1];
        const profileName = prefix ? `${prefix}_std_${profileNumber}` : `Profile_std_${profileNumber}`;
        
        // Create standard profile config
        const standardConfig = {
            user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            language: "en-US,en;q=0.9",
            timezone: "Europe/Berlin",
            webrtc: "disabled",
            window_size: [1920, 1080],
            startup_urls: [],
            remark: `Standard profile ${profileNumber} created via bulk operation`
        };
        
        // Add device type specific settings
        if (deviceType === 'ios') {
            standardConfig.window_size = [375, 667];
            standardConfig.user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1";
        } else if (deviceType === 'android') {
            standardConfig.window_size = [360, 640];
            standardConfig.user_agent = "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36";
        } else if (deviceType === 'windows') {
            standardConfig.window_size = [1920, 1080];
            standardConfig.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
        } else if (deviceType === 'macos') {
            standardConfig.window_size = [1920, 1080];
            standardConfig.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";
        }
        
        const args = ['manager.py', 'create', '--name', profileName, '--config', JSON.stringify(standardConfig)];
        
        const pythonProcess = spawn('python', args, {
            cwd: path.join(__dirname, '..')
        });
        
        let errorOutput = '';
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                createdProfiles.push(profileName);
                console.log(`✅ Created standard profile: ${profileName}`);
            } else {
                if (errorOutput.includes('already exists')) {
                    console.log(`⚠️ Profile '${profileName}' already exists. Skipping.`);
                } else {
                    failedProfiles.push({ name: profileName, error: errorOutput });
                    console.error(`❌ Failed to create standard profile '${profileName}':`, errorOutput);
                }
            }
            
            // Continue with next profile
            setTimeout(createNextStandardProfile, 100);
        });
    }
    
    // Start creating standard profiles sequentially
    createNextStandardProfile();
});

// API for bulk profile deletion
app.post('/api/profiles/bulk-delete', (req, res) => {
    const { names } = req.body;
    const args = ['manager.py', 'bulk-delete', '--names', ...names];
    
    const pythonProcess = spawn('python', args, {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(200).json({ message: `Deleted ${names.length} profiles successfully.` });
        } else {
            console.error('Bulk delete error:', errorOutput);
            res.status(500).json({ error: 'Failed to delete profiles', details: errorOutput });
        }
    });
});

// API to disable proxy for a profile
app.post('/api/profiles/disable-proxy', (req, res) => {
    const { name } = req.body;
    const pythonProcess = spawn('python', ['manager.py', 'disable-proxy', '--name', name], {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(200).json({ message: `Proxy disabled for '${name}'.` });
        } else {
            console.error('Disable proxy error:', errorOutput);
            res.status(500).json({ error: 'Failed to disable proxy', details: errorOutput });
        }
    });
});

// API to rename a profile
app.post('/api/profiles/rename', (req, res) => {
    const { oldName, newName } = req.body;
    const pythonProcess = spawn('python', ['manager.py', 'rename', '--old-name', oldName, '--new-name', newName], {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(200).json({ message: `Profile renamed from '${oldName}' to '${newName}'.` });
        } else {
            console.error('Rename profile error:', errorOutput);
            res.status(500).json({ error: 'Failed to rename profile', details: errorOutput });
        }
    });
});

// API to change proxy for a profile
app.post('/api/profiles/change-proxy', (req, res) => {
    const { name, proxy } = req.body;
    const args = ['manager.py', 'change-proxy', '--name', name];
    if (proxy) args.push('--proxy', proxy);
    
    const pythonProcess = spawn('python', args, {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.status(200).json({ message: `Proxy changed for '${name}'.` });
        } else {
            console.error('Change proxy error:', errorOutput);
            res.status(500).json({ error: 'Failed to change proxy', details: errorOutput });
        }
    });
});

// API to export profiles with data
app.get('/api/profiles/export', (req, res) => {
    const exportPath = path.join(__dirname, 'exports', `profiles_${Date.now()}.zip`);
    
    // Ensure exports directory exists
    const exportsDir = path.dirname(exportPath);
    if (!fs.existsSync(exportsDir)) {
        fs.mkdirSync(exportsDir, { recursive: true });
    }
    
    const pythonProcess = spawn('python', ['manager.py', 'export', '--path', exportPath], {
        cwd: path.join(__dirname, '..')
    });
    
    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            // Send file for download
            res.download(exportPath, 'profiles_export.zip', (err) => {
                if (!err) {
                    // Clean up file after download
                    setTimeout(() => {
                        try { fs.unlinkSync(exportPath); } catch (e) {}
                    }, 5000);
                }
            });
        } else {
            console.error('Export error:', errorOutput);
            res.status(500).json({ error: 'Failed to export profiles', details: errorOutput });
        }
    });
});

// API to import profiles with data
const upload = multer({ dest: path.join(__dirname, 'imports') });

app.post('/api/profiles/import', upload.single('file'), (req, res) => {
    const { overwrite } = req.body;
    
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }
    
    const importPath = req.file.path;
    
    try {
        const args = ['manager.py', 'import', '--path', importPath];
        if (overwrite === 'true') args.push('--overwrite');
        
        const pythonProcess = spawn('python', args, {
            cwd: path.join(__dirname, '..')
        });
        
        let errorOutput = '';
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            // Clean up temporary file
            try { fs.unlinkSync(importPath); } catch (e) {}
            
            if (code === 0) {
                res.status(200).json({ message: 'Profiles imported successfully.' });
            } else {
                console.error('Import error:', errorOutput);
                res.status(500).json({ error: 'Failed to import profiles', details: errorOutput });
            }
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to process import file', details: error.message });
    }
});

// Groups API
app.get('/api/groups', (req, res) => {
    const groups = readJsonFile(GROUPS_FILE, []);
    res.json(groups);
});

app.get('/api/groups/:id/profiles', (req, res) => {
    const groupId = parseInt(req.params.id);
    const groups = readJsonFile(GROUPS_FILE, []);
    const group = groups.find(g => g.id === groupId);
    
    if (group && group.profileList) {
        res.json(group.profileList);
    } else {
        res.json([]);
    }
});

app.post('/api/groups/:id/assign', (req, res) => {
    const groupId = parseInt(req.params.id);
    const { profiles } = req.body;
    const groups = readJsonFile(GROUPS_FILE, []);
    
    const groupIndex = groups.findIndex(g => g.id === groupId);
    if (groupIndex !== -1) {
        if (!groups[groupIndex].profileList) {
            groups[groupIndex].profileList = [];
        }
        
        // Add new profiles (avoid duplicates)
        profiles.forEach(profile => {
            if (!groups[groupIndex].profileList.includes(profile)) {
                groups[groupIndex].profileList.push(profile);
            }
        });
        
        groups[groupIndex].profiles = groups[groupIndex].profileList.length;
        
        if (writeJsonFile(GROUPS_FILE, groups)) {
            res.json({ message: 'Profiles assigned successfully' });
        } else {
            res.status(500).json({ error: 'Failed to assign profiles' });
        }
    } else {
        res.status(404).json({ error: 'Group not found' });
    }
});

app.post('/api/groups', (req, res) => {
    const { name, description } = req.body;
    const groups = readJsonFile(GROUPS_FILE, []);
    
    const newGroup = {
        id: Date.now(),
        name,
        description,
        profiles: 0,
        profileList: [],
        createdAt: new Date().toISOString()
    };
    
    groups.push(newGroup);
    
    if (writeJsonFile(GROUPS_FILE, groups)) {
        res.status(201).json(newGroup);
    } else {
        res.status(500).json({ error: 'Failed to create group' });
    }
});

app.delete('/api/groups/:id', (req, res) => {
    const groupId = parseInt(req.params.id);
    const groups = readJsonFile(GROUPS_FILE, []);
    
    const filteredGroups = groups.filter(group => group.id !== groupId);
    
    if (writeJsonFile(GROUPS_FILE, filteredGroups)) {
        res.json({ message: 'Group deleted successfully' });
    } else {
        res.status(500).json({ error: 'Failed to delete group' });
    }
});

// Proxies API
app.get('/api/proxies', (req, res) => {
    const proxies = readJsonFile(PROXIES_FILE, []);
    res.json(proxies);
});

app.post('/api/proxies', (req, res) => {
    const { name, host, port, username, password, type } = req.body;
    const proxies = readJsonFile(PROXIES_FILE, []);
    
    const newProxy = {
        id: Date.now(),
        name,
        host,
        port,
        username: username || '',
        password: password || '',
        type,
        status: 'active',
        country: 'Unknown',
        createdAt: new Date().toISOString()
    };
    
    proxies.push(newProxy);
    
    if (writeJsonFile(PROXIES_FILE, proxies)) {
        res.status(201).json(newProxy);
    } else {
        res.status(500).json({ error: 'Failed to create proxy' });
    }
});

app.put('/api/proxies/:id/status', (req, res) => {
    const proxyId = parseInt(req.params.id);
    const { status } = req.body;
    const proxies = readJsonFile(PROXIES_FILE, []);
    
    const proxyIndex = proxies.findIndex(proxy => proxy.id === proxyId);
    if (proxyIndex !== -1) {
        proxies[proxyIndex].status = status;
        
        if (writeJsonFile(PROXIES_FILE, proxies)) {
            res.json(proxies[proxyIndex]);
        } else {
            res.status(500).json({ error: 'Failed to update proxy status' });
        }
    } else {
        res.status(404).json({ error: 'Proxy not found' });
    }
});

app.delete('/api/proxies/:id', (req, res) => {
    const proxyId = parseInt(req.params.id);
    const proxies = readJsonFile(PROXIES_FILE, []);
    
    const filteredProxies = proxies.filter(proxy => proxy.id !== proxyId);
    
    if (writeJsonFile(PROXIES_FILE, filteredProxies)) {
        res.json({ message: 'Proxy deleted successfully' });
    } else {
        res.status(500).json({ error: 'Failed to delete proxy' });
    }
});

// Analytics API
app.get('/api/analytics', (req, res) => {
    const analytics = readJsonFile(ANALYTICS_FILE, { sessions: [], stats: {} });
    res.json(analytics);
});

// Settings API
app.get('/api/settings', (req, res) => {
    const settings = readJsonFile(SETTINGS_FILE, {});
    res.json(settings);
});

app.put('/api/settings', (req, res) => {
    const newSettings = req.body;
    
    if (writeJsonFile(SETTINGS_FILE, newSettings)) {
        res.json(newSettings);
    } else {
        res.status(500).json({ error: 'Failed to save settings' });
    }
});

app.listen(PORT, '0.0.0.0', () => console.log(`🚀 Backend server running on http://127.0.0.1:${PORT}`));