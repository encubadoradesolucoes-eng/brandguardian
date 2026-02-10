const express = require('express');
const wppconnect = require('@wppconnect-team/wppconnect');
const fs = require('fs');
const path = require('path');
const app = express();
const PORT = 3002;

app.use(express.json());

let client = null;
let status = 'DISCONNECTED';

// Caminho para comunicar com o Python
const STATIC_DIR = path.join(__dirname, '../static');
if (!fs.existsSync(STATIC_DIR)) fs.mkdirSync(STATIC_DIR);

const QR_FILE = path.join(STATIC_DIR, 'whatsapp_qr.txt');
const STATUS_FILE = path.join(STATIC_DIR, 'whatsapp_status.txt');

// Limpar estado anterior
if (fs.existsSync(QR_FILE)) fs.unlinkSync(QR_FILE);
fs.writeFileSync(STATUS_FILE, 'DISCONNECTED');

console.log('>>> Iniciando BrandGuardian WPP Engine...');

wppconnect.create({
    session: 'brandguardian-session',
    catchQR: (base64Qr) => {
        console.log('>> QR CODE RECEBIDO');
        status = 'QR_CODE';
        fs.writeFileSync(QR_FILE, base64Qr);
        fs.writeFileSync(STATUS_FILE, 'QR_CODE');
    },
    statusFind: (statusSession, session) => {
        console.log('>> Status Sessão:', statusSession);

        if (['isLogged', 'inChat', 'successChat'].includes(statusSession)) {
            status = 'CONNECTED';
            fs.writeFileSync(STATUS_FILE, 'CONNECTED');
            if (fs.existsSync(QR_FILE)) fs.unlinkSync(QR_FILE); // Limpar QR após conectar
        }

        if (['notLogged', 'desconnectedMobile', 'browserClose'].includes(statusSession)) {
            status = 'DISCONNECTED';
            fs.writeFileSync(STATUS_FILE, 'DISCONNECTED');
        }
    },
    headless: true,
    devtools: false,
    useChrome: false,
    debug: false,
    logQR: false,
    browserArgs: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-default-apps',
        '--disable-software-rasterizer',
        '--js-flags="--max-old-space-size=150"'
    ],
    puppeteerOptions: {
        protocolTimeout: 999999,
        userDataDir: path.join(__dirname, 'tokens/puppeteer_cache'),
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--js-flags="--max-old-space-size=150"'
        ]
    },
    sessionToken: {
        WABrowserId: 'brandguardian',
    },
    disableWelcome: true,
    autoClose: 0,
    protocolTimeout: 999999
})
    .then((wpp) => {
        client = wpp;
        status = 'CONNECTED';
        fs.writeFileSync(STATUS_FILE, 'CONNECTED');
        console.log('>>> WhatsApp PRONTO!');
    })
    .catch((err) => {
        console.error('Erro Fatal WPP:', err);
    });

// API para Enviar Texto
app.post('/send', async (req, res) => {
    const { phone, message } = req.body;

    if (!client && status !== 'CONNECTED') {
        return res.status(503).json({ error: 'WhatsApp Offline ou Iniciando' });
    }

    try {
        let cleanPhone = phone.replace(/\D/g, '');
        if (!cleanPhone.startsWith('258')) cleanPhone = '258' + cleanPhone;
        const chatId = cleanPhone + '@c.us';

        await client.sendText(chatId, message);
        res.json({ success: true, id: chatId });
    } catch (e) {
        console.error("Erro envio:", e);
        res.status(500).json({ error: e.toString() });
    }
});

// API para Enviar Arquivo (Cartão)
app.post('/send-file', async (req, res) => {
    const { phone, filePath, caption } = req.body;

    if (!client && status !== 'CONNECTED') return res.status(503).json({ error: 'WhatsApp Offline' });

    try {
        let cleanPhone = phone.replace(/\D/g, '');
        if (!cleanPhone.startsWith('258')) cleanPhone = '258' + cleanPhone;
        const chatId = cleanPhone + '@c.us';

        // Resolver caminho absoluto se necessário
        const absolutePath = path.resolve(filePath);
        console.log(`Enviando arquivo para ${chatId}: ${absolutePath}`);

        await client.sendFile(chatId, absolutePath, 'cartao_visita.png', caption);
        res.json({ success: true });
    } catch (e) {
        console.error("Erro envio arquivo:", e);
        res.status(500).json({ error: e.toString() });
    }
});

app.get('/status', (req, res) => {
    res.json({ status: status });
});

app.listen(PORT, () => console.log(`BrandGuardian WPP Engine rodando na porta ${PORT}`));
