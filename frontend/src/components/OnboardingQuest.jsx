/**
 * OnboardingQuest - 新手三部曲
 *
 * 新用戶引導：三個任務配橫式金色進度環
 * 1. 拍照入庫  2. 揪喝分享  3. 開瓶儀式
 * 全部完成後引導至 Pro Mode
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';
import '../styles/OnboardingQuest.css';

const STORAGE_KEY = 'wine_cellar_onboarding';

const TASKS = [
    {
        key: 'scan',
        icon: '📸',
        doneIcon: '✅',
        label: '拍照入庫',
        encouragement: '🎉 太棒了！第一支酒已入庫！',
        route: '/add',
    },
    {
        key: 'invite',
        icon: '🥂',
        doneIcon: '✅',
        label: '揪喝分享',
        encouragement: '🥂 好酒要跟好友一起喝！',
        route: '/invitation/create',
    },
    {
        key: 'open',
        icon: '🍷',
        doneIcon: '✅',
        label: '開瓶儀式',
        encouragement: '🍷 乾杯！開瓶儀式完成！',
        route: null, // 需要先有酒才能開瓶，不直接跳轉
    },
];

// SVG 進度環
const ProgressRing = ({ done }) => {
    const r = 30;
    const circumference = 2 * Math.PI * r;

    return (
        <svg className="onboarding-quest__ring-svg" viewBox="0 0 72 72">
            <circle className="onboarding-quest__ring-bg" cx="36" cy="36" r={r} />
            <circle
                className={`onboarding-quest__ring-progress${done ? ' onboarding-quest__ring-progress--done' : ''}`}
                cx="36"
                cy="36"
                r={r}
                style={{ strokeDashoffset: done ? 0 : circumference }}
            />
        </svg>
    );
};

// Confetti 粒子
const Confetti = () => {
    const colors = ['#00f0ff', '#ff00ff', '#b967ff', '#00ff88', '#fff', '#00c4cc'];
    const pieces = Array.from({ length: 24 }, (_, i) => ({
        id: i,
        left: `${Math.random() * 100}%`,
        delay: `${Math.random() * 1.5}s`,
        color: colors[i % colors.length],
        size: 4 + Math.random() * 6,
        rotation: Math.random() * 360,
    }));

    return (
        <div className="onboarding-quest__confetti">
            {pieces.map((p) => (
                <div
                    key={p.id}
                    className="onboarding-quest__confetti-piece"
                    style={{
                        left: p.left,
                        top: '-10px',
                        width: p.size,
                        height: p.size,
                        backgroundColor: p.color,
                        animationDelay: p.delay,
                        transform: `rotate(${p.rotation}deg)`,
                    }}
                />
            ))}
        </div>
    );
};

// localStorage 工具
const getOnboardingState = () => {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
};

const setOnboardingState = (state) => {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch { /* ignore */ }
};

const OnboardingQuest = ({ wineItems = [] }) => {
    const navigate = useNavigate();
    const [dismissed, setDismissed] = useState(false);
    const [hasInvitation, setHasInvitation] = useState(false);
    const [showCelebration, setShowCelebration] = useState(false);
    const [newlyCompleted, setNewlyCompleted] = useState(null);

    // 初始化 / 判斷是否在首週內
    const onboardingState = useMemo(() => {
        let state = getOnboardingState();
        if (!state) {
            state = {
                startDate: new Date().toISOString().split('T')[0],
                dismissed: false,
                celebrationShown: false,
                prevCompleted: { scan: false, invite: false, open: false },
            };
            setOnboardingState(state);
        }
        return state;
    }, []);

    // 查詢邀請紀錄
    useEffect(() => {
        if (onboardingState?.dismissed) return;
        const checkInvitations = async () => {
            try {
                const data = await apiClient.get('/invitations');
                if (Array.isArray(data) && data.length > 0) {
                    setHasInvitation(true);
                }
            } catch {
                // 沒有邀請或 API 錯誤，忽略
            }
        };
        checkInvitations();
    }, [onboardingState]);

    // 任務完成狀態
    const taskStatus = useMemo(() => ({
        scan: wineItems.length > 0,  // 修改：有酒款就算完成拍照入庫
        invite: hasInvitation,
        open: wineItems.some((item) => item.bottle_status === 'opened'),
    }), [wineItems, hasInvitation]);

    const completedCount = Object.values(taskStatus).filter(Boolean).length;
    const allDone = completedCount === 3;

    // 偵測新完成的任務
    useEffect(() => {
        if (!onboardingState) return;
        const prev = onboardingState.prevCompleted || {};
        for (const task of TASKS) {
            if (taskStatus[task.key] && !prev[task.key]) {
                setNewlyCompleted(task.key);
                // 更新 localStorage
                const updated = { ...onboardingState, prevCompleted: { ...prev, [task.key]: true } };
                setOnboardingState(updated);
                // 3 秒後清除鼓勵文字
                setTimeout(() => setNewlyCompleted(null), 4000);
                break;
            }
        }
    }, [taskStatus, onboardingState]);

    // 全部完成慶祝
    useEffect(() => {
        if (allDone && !onboardingState?.celebrationShown) {
            setShowCelebration(true);
            setOnboardingState({ ...onboardingState, celebrationShown: true });
        }
    }, [allDone, onboardingState]);

    // 關閉
    const handleDismiss = useCallback(() => {
        setDismissed(true);
        setOnboardingState({ ...onboardingState, dismissed: true });
    }, [onboardingState]);

    // 點擊未完成任務
    const handleTaskClick = useCallback((task) => {
        if (taskStatus[task.key]) return; // 已完成不跳轉
        if (task.route) {
            navigate(task.route);
        } else {
            // 開瓶：沒有直接 route，提示用戶點擊酒款卡片
        }
    }, [taskStatus, navigate]);

    // 不該顯示的情況
    if (dismissed || onboardingState?.dismissed) return null;
    // 全部完成且已看過慶祝，不再顯示
    if (allDone && onboardingState?.celebrationShown && !showCelebration) return null;

    // 找到最近新完成的任務
    const encouragementTask = TASKS.find((t) => t.key === newlyCompleted);

    return (
        <div className="onboarding-quest">
            {/* Confetti */}
            {showCelebration && <Confetti />}

            {/* 關閉按鈕 */}
            <button className="onboarding-quest__close" onClick={handleDismiss}>✕</button>

            {/* 標題 */}
            <div className="onboarding-quest__title">
                <h4>🏆 新手三部曲</h4>
                <p>完成任務，解鎖達人模式</p>
            </div>

            {/* 三個橫式進度環 */}
            <div className="onboarding-quest__rings">
                {TASKS.map((task) => {
                    const done = taskStatus[task.key];
                    return (
                        <div
                            key={task.key}
                            className={`onboarding-quest__task${done ? ' onboarding-quest__task--done' : ''}`}
                            onClick={() => handleTaskClick(task)}
                        >
                            <div className="onboarding-quest__ring-wrap">
                                <ProgressRing done={done} />
                                <span className="onboarding-quest__ring-icon">
                                    {done ? task.doneIcon : task.icon}
                                </span>
                            </div>
                            <span className="onboarding-quest__task-label">{task.label}</span>
                        </div>
                    );
                })}
            </div>

            {/* 進度文字 */}
            <div className="onboarding-quest__progress-text">
                已完成 <span>{completedCount}</span> / 3 項任務
            </div>

            {/* 單項完成鼓勵 */}
            {encouragementTask && !allDone && (
                <div className="onboarding-quest__encouragement">
                    {encouragementTask.encouragement}
                </div>
            )}

            {/* 全部完成慶祝 */}
            {allDone && (
                <div className="onboarding-quest__celebration">
                    <div className="onboarding-quest__celebration-title">
                        🏆 恭喜完成新手三部曲！
                    </div>
                    <div className="onboarding-quest__celebration-text">
                        你已經掌握了酒窖的核心功能 🥂<br />
                        前往「酒窖設定」升級為<strong style={{ color: '#00f0ff' }}>達人模式</strong>，<br />
                        開啟你的品飲筆記，享受好酒時光！
                    </div>
                    <button
                        className="onboarding-quest__celebration-cta"
                        onClick={() => navigate('/settings/cellar')}
                    >
                        前往設定 →
                    </button>
                </div>
            )}
        </div>
    );
};

export default OnboardingQuest;
