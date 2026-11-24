package com.worldwalker.app;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.view.View;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String TAG = "WorldWalker";
    private static final int REQ_PICK_FILE = 0x5701;
    private static final int MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024;

    private WebView webView;
    private LinearLayout loading;
    private TextView loadingStatus;
    private TextView loadingError;
    private ProgressBar loadingSpinner;
    private Button retryButton;

    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private ValueCallback<Uri[]> pendingFileCallback;
    private File runtimeDir;
    private int port;
    private boolean contentShown;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        getWindow().setStatusBarColor(Color.parseColor("#241F18"));
        getWindow().setNavigationBarColor(Color.parseColor("#241F18"));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            getWindow().setStatusBarContrastEnforced(false);
            getWindow().setNavigationBarContrastEnforced(false);
        }

        webView = findViewById(R.id.webview);
        loading = findViewById(R.id.loading);
        loadingStatus = findViewById(R.id.loading_status);
        loadingError = findViewById(R.id.loading_error);
        loadingSpinner = findViewById(R.id.loading_spinner);
        retryButton = findViewById(R.id.retry);

        configureWebView();
        retryButton.setOnClickListener(v -> bootEngine());
        bootEngine();
    }

    private void configureWebView() {
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setSaveFormData(false);
        settings.setSupportMultipleWindows(false);
        settings.setTextZoom(100);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setUserAgentString(settings.getUserAgentString() + " WorldWalkerAndroid/1.20.0");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && Build.VERSION.SDK_INT < 33) {
            settings.setForceDark(WebSettings.FORCE_DARK_OFF);
        }
        if (Build.VERSION.SDK_INT >= 33) {
            settings.setAlgorithmicDarkeningAllowed(false);
        }

        webView.setBackgroundColor(Color.parseColor("#F3EEE2"));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return openExternally(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return openExternally(Uri.parse(url));
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (!contentShown && url != null && url.startsWith("http://127.0.0.1:")) {
                    contentShown = true;
                    webView.setVisibility(View.VISIBLE);
                    loading.animate().alpha(0f).setDuration(260).withEndAction(() -> {
                        loading.setVisibility(View.GONE);
                        loading.setAlpha(1f);
                    });
                }
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showError("页面加载失败：" + error.getDescription());
                }
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (pendingFileCallback != null) {
                    pendingFileCallback.onReceiveValue(null);
                }
                pendingFileCallback = callback;
                Intent intent = params.createIntent();
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                try {
                    startActivityForResult(intent, REQ_PICK_FILE);
                } catch (Exception exc) {
                    pendingFileCallback = null;
                    callback.onReceiveValue(null);
                    toast(getString(R.string.no_file_app) + "：" + shortMessage(exc));
                }
                return true;
            }
        });

        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition,
                                        String mimeType, long contentLength) {
                beginDownload(url, contentDisposition, mimeType);
            }
        });
    }

    private boolean openExternally(Uri uri) {
        if (uri == null) return false;
        String host = uri.getHost();
        if ("127.0.0.1".equals(host) || "localhost".equals(host)) return false;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (Exception exc) {
            toast("没有可以打开这个链接的应用");
        }
        return true;
    }

    private void bootEngine() {
        if (port > 0) {
            loadPanel();
            return;
        }
        showLoading(getString(R.string.loading_subtitle));
        io.execute(this::startEngine);
    }

    private void startEngine() {
        try {
            runtimeDir = extractRuntime();
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(getApplicationContext()));
            }
            File filesDir = new File(getFilesDir().getCanonicalPath());
            File cacheRoot = new File(getCacheDir().getCanonicalPath());
            File gameDir = new File(filesDir, "game");
            File homeDir = new File(filesDir, "home");
            File cacheDir = new File(cacheRoot, "python");
            PyObject module = Python.getInstance().getModule("world_walker_android");
            int p = module.callAttr("start_server",
                    runtimeDir.getAbsolutePath(),
                    gameDir.getAbsolutePath(),
                    homeDir.getAbsolutePath(),
                    cacheDir.getAbsolutePath()).toInt();
            if (p <= 0) throw new IllegalStateException("面板没有返回端口");
            port = p;
            runOnUiThread(this::loadPanel);
        } catch (Throwable exc) {
            Log.e(TAG, "engine boot failed", exc);
            runOnUiThread(() -> showError(shortMessage(exc)));
        }
    }

    private void loadPanel() {
        if (port <= 0) return;
        contentShown = false;
        webView.loadUrl("http://127.0.0.1:" + port + "/");
    }

    private File extractRuntime() throws IOException {
        File base = new File(new File(getFilesDir().getCanonicalPath()), "runtime");
        File target = new File(base, "v" + BuildConfig.VERSION_CODE);
        File ready = new File(target, ".ready");
        if (ready.isFile()) return target;
        deleteRecursively(target);
        if (!target.mkdirs() && !target.isDirectory()) {
            throw new IOException("无法创建运行时目录");
        }
        String root = target.getCanonicalPath() + File.separator;
        long bytes = 0;
        try (InputStream raw = getAssets().open("runtime.zip");
             java.util.zip.ZipInputStream zip = new java.util.zip.ZipInputStream(raw)) {
            java.util.zip.ZipEntry entry;
            byte[] buffer = new byte[8192];
            while ((entry = zip.getNextEntry()) != null) {
                String name = entry.getName();
                if (name.startsWith("/") || name.contains("..")) {
                    throw new IOException("runtime.zip 路径非法：" + name);
                }
                File out = new File(target, name);
                if (!out.getCanonicalPath().startsWith(root)) {
                    throw new IOException("runtime.zip 越界：" + name);
                }
                if (entry.isDirectory()) {
                    if (!out.mkdirs() && !out.isDirectory()) throw new IOException("无法创建 " + name);
                    continue;
                }
                File parent = out.getParentFile();
                if (parent != null && !parent.mkdirs() && !parent.isDirectory()) {
                    throw new IOException("无法创建目录 " + parent);
                }
                try (OutputStream os = new FileOutputStream(out)) {
                    int n;
                    while ((n = zip.read(buffer)) > 0) {
                        os.write(buffer, 0, n);
                        bytes += n;
                    }
                }
            }
        }
        if (bytes < 100_000) throw new IOException("runtime.zip 内容异常（" + bytes + " bytes）");
        try (FileOutputStream marker = new FileOutputStream(ready)) {
            marker.write("1.20.0\n".getBytes(StandardCharsets.UTF_8));
        }
        cleanOldRuntimes(target);
        return target;
    }

    private void cleanOldRuntimes(File keep) {
        File[] children = keep.getParentFile() == null ? null : keep.getParentFile().listFiles();
        if (children == null) return;
        for (File child : children) {
            if (child.isDirectory() && !child.equals(keep)) deleteRecursively(child);
        }
    }

    private void deleteRecursively(File file) {
        if (file == null || !file.exists()) return;
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) for (File child : children) deleteRecursively(child);
        }
        //noinspection ResultOfMethodCallIgnored
        file.delete();
    }

    private void beginDownload(String url, String contentDisposition, String mimeType) {
        final String filename = filenameFrom(contentDisposition, url, mimeType);
        final String mime = normalizeMime(mimeType, filename);
        io.execute(() -> {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    byte[] bytes = fetch(url);
                    saveViaMediaStore(filename, mime, bytes);
                } else {
                    DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                    request.setTitle(filename);
                    request.setDescription("World Walker");
                    request.setMimeType(mime);
                    request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS,
                            "World Walker/" + filename);
                    DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                    if (manager == null) throw new IOException("系统下载服务不可用");
                    manager.enqueue(request);
                }
                toast(getString(R.string.download_saved) + " · " + filename);
            } catch (Throwable exc) {
                Log.e(TAG, "download failed", exc);
                toast(getString(R.string.download_failed) + "：" + shortMessage(exc));
            }
        });
    }

    private byte[] fetch(String url) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setConnectTimeout(8000);
        conn.setReadTimeout(30000);
        conn.setRequestMethod("GET");
        conn.setInstanceFollowRedirects(true);
        int code = conn.getResponseCode();
        if (code != 200) throw new IOException("HTTP " + code);
        try (InputStream in = conn.getInputStream();
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int n;
            int total = 0;
            while ((n = in.read(buffer)) > 0) {
                total += n;
                if (total > MAX_DOWNLOAD_BYTES) throw new IOException("文件超过 32 MB");
                out.write(buffer, 0, n);
            }
            return out.toByteArray();
        } finally {
            conn.disconnect();
        }
    }

    private void saveViaMediaStore(String filename, String mime, byte[] bytes) throws IOException {
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
        values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/World Walker");
        values.put(MediaStore.MediaColumns.IS_PENDING, 1);
        Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IOException("无法创建下载条目");
        try (OutputStream out = getContentResolver().openOutputStream(uri)) {
            if (out == null) throw new IOException("无法写入下载条目");
            out.write(bytes);
        }
        ContentValues done = new ContentValues();
        done.put(MediaStore.MediaColumns.IS_PENDING, 0);
        getContentResolver().update(uri, done, null, null);
    }

    private static String filenameFrom(String contentDisposition, String url, String mimeType) {
        String name = null;
        if (contentDisposition != null) {
            for (String part : contentDisposition.split(";")) {
                String item = part.trim();
                if (item.startsWith("filename*=")) {
                    String value = item.substring("filename*=".length()).trim();
                    int sep = value.indexOf("''");
                    if (sep >= 0) value = value.substring(sep + 2);
                    try {
                        name = URLDecoder.decode(value, "UTF-8");
                    } catch (Exception ignored) {
                        name = value;
                    }
                } else if (item.startsWith("filename=")) {
                    name = item.substring("filename=".length()).trim().replace("\"", "");
                }
            }
        }
        if (name == null || name.trim().isEmpty()) {
            try {
                String path = Uri.parse(url).getLastPathSegment();
                if (path != null && !path.isEmpty()) name = path;
            } catch (Exception ignored) {
                // fall through
            }
        }
        if (name == null || name.trim().isEmpty()) {
            name = "world-walker-export." + extensionFor(mimeType);
        }
        name = name.replace('\\', '_').replace('/', '_')
                .replace(':', '_').replace('*', '_').replace('?', '_')
                .replace('"', '_').replace('<', '_').replace('>', '_')
                .replace('|', '_').replace('\n', '_').replace('\r', '_').trim();
        while (name.startsWith(".")) name = name.substring(1);
        if (name.isEmpty()) name = "world-walker-export." + extensionFor(mimeType);
        if (name.length() > 120) {
            int dot = name.lastIndexOf('.');
            String ext = dot >= 0 ? name.substring(dot) : "";
            name = name.substring(0, Math.max(1, 120 - ext.length())) + ext;
        }
        return name;
    }

    private static String normalizeMime(String mimeType, String filename) {
        if (mimeType != null && !mimeType.isEmpty() && !"application/octet-stream".equals(mimeType)) {
            return mimeType;
        }
        String lower = filename.toLowerCase();
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".md")) return "text/markdown";
        if (lower.endsWith(".zip")) return "application/zip";
        if (lower.endsWith(".png")) return "image/png";
        return "application/octet-stream";
    }

    private static String extensionFor(String mimeType) {
        if (mimeType == null) return "bin";
        if (mimeType.contains("json")) return "json";
        if (mimeType.contains("markdown")) return "md";
        if (mimeType.contains("zip")) return "zip";
        if (mimeType.contains("png")) return "png";
        return "bin";
    }

    private void showLoading(String message) {
        loading.setVisibility(View.VISIBLE);
        loading.setAlpha(1f);
        loadingStatus.setText(message);
        loadingStatus.setVisibility(View.VISIBLE);
        loadingError.setVisibility(View.GONE);
        loadingSpinner.setVisibility(View.VISIBLE);
        retryButton.setVisibility(View.GONE);
        webView.setVisibility(View.INVISIBLE);
    }

    private void showError(String message) {
        contentShown = false;
        loading.setVisibility(View.VISIBLE);
        loading.setAlpha(1f);
        loadingStatus.setText(R.string.loading_failed);
        loadingStatus.setVisibility(View.VISIBLE);
        loadingError.setText(message == null ? getString(R.string.loading_failed_note) : message);
        loadingError.setVisibility(View.VISIBLE);
        loadingSpinner.setVisibility(View.GONE);
        retryButton.setVisibility(View.VISIBLE);
        webView.setVisibility(View.INVISIBLE);
    }

    private static String shortMessage(Throwable exc) {
        String message = exc.getMessage();
        if (message == null || message.trim().isEmpty()) message = exc.getClass().getSimpleName();
        if (message.length() > 500) message = message.substring(0, 500) + "…";
        return message;
    }

    private void toast(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_LONG).show());
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_PICK_FILE) {
            if (pendingFileCallback != null) {
                Uri[] result = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
                pendingFileCallback.onReceiveValue(result);
                pendingFileCallback = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onBackPressed() {
        if (webView == null || port <= 0) {
            finish();
            return;
        }
        webView.evaluateJavascript(
                "(function(){try{return window.wwAndroidBack ? window.wwAndroidBack() : false;}catch(e){return false;}})()",
                value -> {
                    if (!"true".equals(value)) finish();
                });
    }

    @Override
    protected void onPause() {
        if (webView != null) webView.onPause();
        super.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) webView.onResume();
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.destroy();
            webView = null;
        }
        try {
            if (Python.isStarted()) {
                Python.getInstance().getModule("world_walker_android").callAttr("stop_server");
            }
        } catch (Throwable exc) {
            Log.w(TAG, "stop_server failed", exc);
        }
        io.shutdownNow();
        super.onDestroy();
    }
}
