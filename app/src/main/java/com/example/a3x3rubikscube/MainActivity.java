package com.example.a3x3rubikscube;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    private EditText inputEditText;
    private TextView resultTextView;
    private static final int SCAN_REQUEST_CODE = 100;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        
        // 設定 Window Insets
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        // 初始化 Python 環境
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        // 初始化 UI 元件
        inputEditText = findViewById(R.id.inputEditText);
        resultTextView = findViewById(R.id.resultTextView);
        Button solveButton = findViewById(R.id.solveButton);
        Button scanButton = findViewById(R.id.scanButton);

        solveButton.setOnClickListener(v -> {
            String input = inputEditText.getText().toString().trim();
            if (input.isEmpty()) {
                Toast.makeText(this, "請輸入方塊字串", Toast.LENGTH_SHORT).show();
                return;
            }
            solveCubeWithPython(input);
        });

        scanButton.setOnClickListener(v -> {
            Intent intent = new Intent(this, ScanActivity.class);
            startActivityForResult(intent, SCAN_REQUEST_CODE);
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == SCAN_REQUEST_CODE && resultCode == RESULT_OK) {
            String cubeString = data.getStringExtra("cubeString");
            if (cubeString != null) {
                inputEditText.setText(cubeString);
                solveCubeWithPython(cubeString);
            }
        }
    }

    private void solveCubeWithPython(String cubeString) {
        try {
            Python py = Python.getInstance();
            // 載入 solver_core.py 模組
            PyObject solverModule = py.getModule("solver_core");
            // 呼叫 solve_cube 函式
            PyObject result = solverModule.callAttr("solve_cube", cubeString);
            
            // 顯示結果
            resultTextView.setText(result.toString());
        } catch (Exception e) {
            resultTextView.setText("執行錯誤: " + e.getMessage());
        }
    }
}
