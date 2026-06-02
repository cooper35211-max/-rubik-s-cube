package com.example.a3x3rubikscube;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.util.AttributeSet;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.util.List;

public class OverlayView extends View {
    private Paint linePaint;
    private Paint pointPaint;
    private List<float[]> corners; // [[x,y], [x,y], [x,y], [x,y]]
    private Path borderPath;

    public OverlayView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        linePaint = new Paint();
        linePaint.setColor(Color.GREEN);
        linePaint.setStrokeWidth(8f);
        linePaint.setStyle(Paint.Style.STROKE);

        pointPaint = new Paint();
        pointPaint.setColor(Color.RED);
        pointPaint.setStyle(Paint.Style.FILL);

        borderPath = new Path();
    }

    public void setResults(List<float[]> corners) {
        this.corners = corners;
        invalidate(); // Redraw
    }

    @Override
    protected void onDraw(@NonNull Canvas canvas) {
        super.onDraw(canvas);

        if (corners != null && corners.size() == 4) {
            borderPath.reset();
            borderPath.moveTo(corners.get(0)[0], corners.get(0)[1]);
            borderPath.lineTo(corners.get(1)[0], corners.get(1)[1]);
            borderPath.lineTo(corners.get(2)[0], corners.get(2)[1]);
            borderPath.lineTo(corners.get(3)[0], corners.get(3)[1]);
            borderPath.close();
            canvas.drawPath(borderPath, linePaint);

            for (float[] corner : corners) {
                canvas.drawCircle(corner[0], corner[1], 10f, pointPaint);
            }
        }
    }
}
