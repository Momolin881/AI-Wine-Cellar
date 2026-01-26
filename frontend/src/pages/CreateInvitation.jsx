
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import liff from '@line/liff';
import {
    Box,
    Typography,
    TextField,
    Button,
    Grid,
    Card,
    CardMedia,
    CardContent,
    Checkbox,
    FormControlLabel,
    Snackbar,
    Alert
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { zhTW } from 'date-fns/locale';

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const CreateInvitation = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        event_time: new Date(),
        location: '',
        theme_image_url: 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
    });

    const [availableWines, setAvailableWines] = useState([]);
    const [selectedWines, setSelectedWines] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    // Fetch wines from backend
    useEffect(() => {
        const fetchWines = async () => {
            try {
                // TODO: Replace with actual API call
                // const response = await fetch(`${API_BASE_URL}/wine-items`);
                // const data = await response.json();

                // Mock data for now to ensure UI works first
                const mockWines = [
                    { id: 1, name: 'Chateau Margaux 2015', image_url: 'https://via.placeholder.com/150' },
                    { id: 2, name: 'Opus One 2018', image_url: 'https://via.placeholder.com/150' },
                    { id: 3, name: 'Penfolds Grange 2016', image_url: 'https://via.placeholder.com/150' },
                ];
                setAvailableWines(mockWines);
            } catch (err) {
                console.error("Failed to fetch wines", err);
            }
        };
        fetchWines();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleDateChange = (newValue) => {
        setFormData(prev => ({ ...prev, event_time: newValue }));
    };

    const handleWineToggle = (wineId) => {
        setSelectedWines(prev => {
            if (prev.includes(wineId)) {
                return prev.filter(id => id !== wineId);
            } else {
                return [...prev, wineId];
            }
        });
    };

    const handleSubmit = async () => {
        if (!formData.title || !formData.event_time) {
            setError("請填寫必填欄位 (標題、時間)");
            return;
        }

        setLoading(true);
        try {
            // 1. Call Backend API to create invitation
            const payload = {
                ...formData,
                wine_ids: selectedWines
            };

            const response = await fetch(`${API_BASE_URL}/invitations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('無法建立邀請');
            }

            const data = await response.json();
            const flexMessage = data.flex_message;

            // 2. Use LIFF shareTargetPicker to send message
            if (liff.isApiAvailable('shareTargetPicker')) {
                const res = await liff.shareTargetPicker([flexMessage]);
                if (res) {
                    setSuccessMsg("邀請已成功發送！");
                    setTimeout(() => navigate('/'), 2000);
                } else {
                    setSuccessMsg("已建立邀請，但未發送訊息。");
                }
            } else {
                // Fallback: Show link to copy
                setSuccessMsg("建立成功！請複製連結分享 (您的 LINE 版本不支援直接發送)");
            }

        } catch (err) {
            console.error(err);
            setError(err.message || "發生錯誤");
        } finally {
            setLoading(false);
        }
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={zhTW}>
            <Box sx={{ p: 2, pb: 10, bgcolor: '#121212', minHeight: '100vh', color: '#fff' }}>
                <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold', color: '#c9a227' }}>
                    發起品飲聚會
                </Typography>

                <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                        label="聚會標題"
                        name="title"
                        value={formData.title}
                        onChange={handleInputChange}
                        fullWidth
                        required
                        sx={{
                            '& .MuiOutlinedInput-root': { color: '#fff', '& fieldset': { borderColor: '#444' } },
                            '& .MuiInputLabel-root': { color: '#888' }
                        }}
                    />

                    <DateTimePicker
                        label="聚會時間"
                        value={formData.event_time}
                        onChange={handleDateChange}
                        sx={{
                            '& .MuiOutlinedInput-root': { color: '#fff', '& fieldset': { borderColor: '#444' } },
                            '& .MuiInputLabel-root': { color: '#888' },
                            '& .MuiSvgIcon-root': { color: '#c9a227' }
                        }}
                    />

                    <TextField
                        label="地點 (選填)"
                        name="location"
                        value={formData.location}
                        onChange={handleInputChange}
                        fullWidth
                        sx={{
                            '& .MuiOutlinedInput-root': { color: '#fff', '& fieldset': { borderColor: '#444' } },
                            '& .MuiInputLabel-root': { color: '#888' }
                        }}
                    />

                    <Typography variant="h6" sx={{ mt: 2, color: '#c9a227' }}>
                        選擇酒款 ({selectedWines.length})
                    </Typography>

                    <Grid container spacing={2}>
                        {availableWines.map(wine => (
                            <Grid item xs={6} key={wine.id}>
                                <Card sx={{ bgcolor: '#2d2d2d', color: '#fff', border: selectedWines.includes(wine.id) ? '1px solid #c9a227' : 'none' }}>
                                    <CardMedia
                                        component="img"
                                        height="100"
                                        image={wine.image_url}
                                        alt={wine.name}
                                    />
                                    <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                                        <FormControlLabel
                                            control={
                                                <Checkbox
                                                    checked={selectedWines.includes(wine.id)}
                                                    onChange={() => handleWineToggle(wine.id)}
                                                    sx={{ color: '#c9a227', '&.Mui-checked': { color: '#c9a227' } }}
                                                />
                                            }
                                            label={
                                                <Typography variant="body2" noWrap sx={{ width: '100px' }}>
                                                    {wine.name}
                                                </Typography>
                                            }
                                        />
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>

                    <Button
                        variant="contained"
                        onClick={handleSubmit}
                        disabled={loading}
                        sx={{ mt: 4, bgcolor: '#c9a227', color: '#000', fontWeight: 'bold', '&:hover': { bgcolor: '#b08d22' } }}
                    >
                        {loading ? '處理中...' : '建立邀請並分享'}
                    </Button>
                </Box>

                <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError('')}>
                    <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>
                </Snackbar>

                <Snackbar open={!!successMsg} autoHideDuration={6000} onClose={() => setSuccessMsg('')}>
                    <Alert severity="success" sx={{ width: '100%' }}>{successMsg}</Alert>
                </Snackbar>
            </Box>
        </LocalizationProvider>
    );
};

export default CreateInvitation;
