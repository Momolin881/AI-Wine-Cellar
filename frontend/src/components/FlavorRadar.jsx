import React from 'react';
import { theme } from 'antd';

/**
 * FlavorRadar - 五角形風味雷達圖
 * 
 * @param {Object} data - { acidity, tannin, body, sweetness, alcohol_feel } (Values: 1-5)
 * @param {Boolean} isChill - Chill Mode (Neon) or Pro Mode (Gold)
 */
const FlavorRadar = ({ data, isChill = false }) => {
    // 預設值 3 (中間)
    const {
        acidity = 3,
        tannin = 3,
        body = 3,
        sweetness = 3,
        alcohol_feel = 3
    } = data || {};

    const size = 200;
    const center = size / 2;
    const radius = 80;

    // 軸線標籤
    const axes = [
        { name: '酸度', value: acidity, angle: -90 },    // Top
        { name: '單寧', value: tannin, angle: -18 },     // Top Right
        { name: '酒體', value: body, angle: 54 },        // Bottom Right
        { name: '酒感', value: alcohol_feel, angle: 126 }, // Bottom Left
        { name: '甜度', value: sweetness, angle: 198 }   // Top Left
    ];

    // Helper: 計算座標
    const getPoint = (value, angle, max = 5) => {
        const rad = (Math.PI / 180) * angle;
        const dist = (value / max) * radius;
        return {
            x: center + dist * Math.cos(rad),
            y: center + dist * Math.sin(rad)
        };
    };

    // 計算多邊形路徑 (外框 max=5)
    const outerPoints = axes.map(axis => getPoint(5, axis.angle)).map(p => `${p.x},${p.y}`).join(' ');

    // 計算內網格 (1-4)
    const gridPoints = [1, 2, 3, 4].map(level =>
        axes.map(axis => getPoint(level, axis.angle)).map(p => `${p.x},${p.y}`).join(' ')
    );

    // 計算資料多邊形
    const dataPoints = axes.map(axis => getPoint(axis.value || 0, axis.angle)).map(p => `${p.x},${p.y}`).join(' ');

    // 顏色設定
    const primaryColor = isChill ? '#00f0ff' : '#c9a227';
    const fillColor = isChill ? 'rgba(0, 240, 255, 0.3)' : 'rgba(201, 162, 39, 0.3)';
    const textColor = isChill ? '#e0e0e0' : '#888';

    return (
        <div style={{ width: size, height: size, margin: '0 auto', position: 'relative' }}>
            <svg width={size} height={size} style={{ overflow: 'visible' }}>
                {/* 網格背景 */}
                <polygon points={outerPoints} fill="none" stroke="#444" strokeWidth="1" />
                {gridPoints.map((points, i) => (
                    <polygon key={i} points={points} fill="none" stroke="#333" strokeDasharray="4 4" />
                ))}

                {/* 軸線 */}
                {axes.map((axis, i) => {
                    const p = getPoint(5, axis.angle);
                    return <line key={i} x1={center} y1={center} x2={p.x} y2={p.y} stroke="#333" />;
                })}

                {/* 資料區域 */}
                <polygon
                    points={dataPoints}
                    fill={fillColor}
                    stroke={primaryColor}
                    strokeWidth="2"
                    style={{ transition: 'all 0.3s ease' }}
                />

                {/* 頂點圓點 */}
                {axes.map((axis, i) => {
                    const p = getPoint(axis.value || 0, axis.angle);
                    return (
                        <circle
                            key={i}
                            cx={p.x}
                            cy={p.y}
                            r="4"
                            fill={primaryColor}
                            style={{ transition: 'all 0.3s ease' }}
                        />
                    );
                })}

                {/* 文字標籤 (簡易定位) */}
                {axes.map((axis, i) => {
                    const labelP = getPoint(6.5, axis.angle); // 稍微外擴
                    return (
                        <text
                            key={i}
                            x={labelP.x}
                            y={labelP.y}
                            fill={textColor}
                            fontSize="12"
                            textAnchor="middle"
                            dominantBaseline="middle"
                        >
                            {axis.name}
                        </text>
                    );
                })}
            </svg>
        </div>
    );
};

export default FlavorRadar;
