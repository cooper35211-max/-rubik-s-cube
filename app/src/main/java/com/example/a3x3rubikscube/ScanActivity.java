package com.example.a3x3rubikscube;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Matrix;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.ImageProxy;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.google.common.util.concurrent.ListenableFuture;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ScanActivity extends AppCompatActivity {
    private static final String TAG = "ScanActivity";
    private static final int REQUEST_CODE_PERMISSIONS = 10;
    private static final String[] REQUIRED_PERMISSIONS = new String[]{Manifest.permission.CAMERA};

    private PreviewView viewFinder;
    private OverlayView overlayView;
    private TextView hintTextView;
    private TextView statusTextView;
    private Button captureButton;

    private ExecutorService cameraExecutor;
    private Python py;
    private PyObject androidScanner;

    private int currentFaceIdx = 0;
    private final String[] faceOrders = {"U", "R", "F", "D", "L", "B"};
    private final String[] faceNames = {"白色面 (頂)", "紅色面 (右)", "綠色面 (前)", "黃色面 (底)", "橘色面 (左)", "藍色面 (後)"};
    private final Map<String, String> facesData = new HashMap<>();
    
    private String lastDetectedColors = "";
    private List<float[]> lastCorners = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_scan);

        viewFinder = findViewById(R.id.viewFinder);
        overlayView = findViewById(R.id.overlayView);
        hintTextView = findViewById(R.id.hintTextView);
        statusTextView = findViewById(R.id.statusTextView);
        captureButton = findViewById(R.id.captureButton);

        py = Python.getInstance();
        androidScanner = py.getModule("android_scanner");

        if (allPermissionsGranted()) {
            startCamera();
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS);
        }

        captureButton.setOnClickListener(v -> {
            if (lastCorners != null && !lastDetectedColors.contains("?")) {
                facesData.put(faceOrders[currentFaceIdx], lastDetectedColors);
                currentFaceIdx++;
                if (currentFaceIdx < 6) {
                    updateUI();
                } else {
                    finishScanning();
                }
            } else {
                Toast.makeText(this, "請確保方塊完全對準且顏色清晰", Toast.LENGTH_SHORT).show();
            }
        });

        cameraExecutor = Executors.newSingleThreadExecutor();
        updateUI();
    }

    private void updateUI() {
        hintTextView.setText("請掃描 " + faceNames[currentFaceIdx] + " (" + faceOrders[currentFaceIdx] + ")");
    }

    private void finishScanning() {
        StringBuilder sb = new StringBuilder();
        for (String face : faceOrders) {
            sb.append(facesData.get(face));
        }
        Intent data = new Intent();
        data.putExtra("cubeString", sb.toString());
        setResult(RESULT_OK, data);
        finish();
    }

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> cameraProviderFuture = ProcessCameraProvider.getInstance(this);

        cameraProviderFuture.addListener(() -> {
            try {
                ProcessCameraProvider cameraProvider = cameraProviderFuture.get();

                Preview preview = new Preview.Builder().build();
                preview.setSurfaceProvider(viewFinder.getSurfaceProvider());

                ImageAnalysis imageAnalysis = new ImageAnalysis.Builder()
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build();

                imageAnalysis.setAnalyzer(cameraExecutor, image -> {
                    processImage(image);
                });

                CameraSelector cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA;

                cameraProvider.unbindAll();
                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageAnalysis);

            } catch (ExecutionException | InterruptedException e) {
                Log.e(TAG, "Use case binding failed", e);
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void processImage(ImageProxy image) {
        // 將 ImageProxy 轉換為 Bitmap 並旋轉
        Bitmap bitmap = imageToBitmap(image);
        image.close();

        if (bitmap == null) return;

        // 轉換為 JPEG bytes 傳給 Python
        ByteArrayOutputStream stream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, stream);
        byte[] byteArray = stream.toByteArray();

        try {
            PyObject result = androidScanner.callAttr("process_frame", byteArray, bitmap.getWidth(), bitmap.getHeight());
            Map<PyObject, PyObject> resultMap = result.asMap();
            
            String status = resultMap.get(py.getBuiltins().get("str").call("status")).toString();
            
            runOnUiThread(() -> {
                if ("success".equals(status)) {
                    statusTextView.setText("已偵測到方塊");
                    
                    // 解析頂點
                    PyObject cornersPy = resultMap.get(py.getBuiltins().get("str").call("corners"));
                    List<PyObject> cornersList = cornersPy.asList();
                    List<float[]> corners = new ArrayList<>();
                    for (PyObject pt : cornersList) {
                        List<PyObject> coord = pt.asList();
                        corners.add(new float[]{coord.get(0).toFloat(), coord.get(1).toFloat()});
                    }
                    
                    lastCorners = corners;
                    lastDetectedColors = resultMap.get(py.getBuiltins().get("str").call("colors")).toString();
                    overlayView.setResults(corners);
                } else {
                    statusTextView.setText("未偵測到方塊");
                    lastCorners = null;
                    overlayView.setResults(null);
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "Python processing error", e);
        }
    }

    private Bitmap imageToBitmap(ImageProxy image) {
        ByteBuffer yBuffer = image.getPlanes()[0].getBuffer();
        ByteBuffer uBuffer = image.getPlanes()[1].getBuffer();
        ByteBuffer vBuffer = image.getPlanes()[2].getBuffer();

        int ySize = yBuffer.remaining();
        int uSize = uBuffer.remaining();
        int vSize = vBuffer.remaining();

        byte[] nv21 = new byte[ySize + uSize + vSize];

        yBuffer.get(nv21, 0, ySize);
        vBuffer.get(nv21, ySize, vSize);
        uBuffer.get(nv21, ySize + vSize, uSize);

        android.graphics.YuvImage yuvImage = new android.graphics.YuvImage(nv21, android.graphics.ImageFormat.NV21, image.getWidth(), image.getHeight(), null);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        yuvImage.compressToJpeg(new android.graphics.Rect(0, 0, image.getWidth(), image.getHeight()), 100, out);
        byte[] imageBytes = out.toByteArray();
        Bitmap bitmap = android.graphics.BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
        
        // 旋轉
        Matrix matrix = new Matrix();
        matrix.postRotate(image.getImageInfo().getRotationDegrees());
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);
    }

    private boolean allPermissionsGranted() {
        for (String permission : REQUIRED_PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera();
            } else {
                Toast.makeText(this, "需要相機權限才能掃描", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        cameraExecutor.shutdown();
    }
}
