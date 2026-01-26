
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Card,
    CardMedia,
    CardContent,
    Grid,
    Button,
    Chip,
    Divider,
    Avatar,
    Stack,
    CircularProgress
} from '@mui/material';
import {
    CalendarMonth,
    LocationOn,
    WineBar,
    AccessTime
} from '@mui/icons-material';
import { format } from 'date-fns';
import { zhTW } from 'date-fns/locale';

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const InvitationDetail = () => {
    const { id } = useParams();
    const [invitation, setInvitation] = useState(null);
    const [wines, setWines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchInvitation = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/invitations/${id}`);
                if (!response.ok) {
                    throw new Error('找不到此邀請函');
                }
                const data = await response.json();
                setInvitation(data.invitation);
                setWines(data.wines);
            } catch (err) {
                console.error(err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchInvitation();
        }
    }, [id]);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', bgcolor: '#121212', color: '#c9a227' }}>
                <CircularProgress color="inherit" />
            </Box>
        );
    }

    if (error || !invitation) {
        return (
            <Box sx={{ p: 4, textAlign: 'center', bgcolor: '#121212', minHeight: '100vh', color: '#fff' }}>
                <Typography variant="h6" color="error">
                    {error || '邀請函失效或已被刪除'}
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ pb: 10, bgcolor: '#121212', minHeight: '100vh', color: '#fff' }}>
            {/* Hero Image */}
            <Box sx={{ position: 'relative', height: '250px' }}>
                <img
                    src={invitation.theme_image_url || 'https://via.placeholder.com/800x400'}
                    alt="Cover"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.7)' }}
                />
                <Box sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: '100%',
                    p: 3,
                    background: 'linear-gradient(to top, #121212, transparent)'
                }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#c9a227', textShadow: '2px 2px 4px rgba(0,0,0,0.8)' }}>
                        {invitation.title}
                    </Typography>
                </Box>
            </Box>

            <Box sx={{ p: 3 }}>
                {/* Event Details */}
                <Stack spacing={2} sx={{ mb: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <CalendarMonth sx={{ color: '#c9a227' }} />
                        <Box>
                            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                {format(new Date(invitation.event_time), 'yyyy年MM月dd日 (EEEE)', { locale: zhTW })}
                            </Typography>
                            <Typography variant="body2" color="gray">
                                {format(new Date(invitation.event_time), 'HH:mm')}
                            </Typography>
                        </Box>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <LocationOn sx={{ color: '#c9a227' }} />
                        <Typography variant="body1">
                            {invitation.location || '地點待定'}
                        </Typography>
                    </Box>

                    {invitation.description && (
                        <Typography variant="body2" color="gray" sx={{ pl: 5, borderLeft: '2px solid #333' }}>
                            {invitation.description}
                        </Typography>
                    )}
                </Stack>

                <Divider sx={{ my: 3, borderColor: '#333' }} />

                {/* Wine List */}
                <Typography variant="h6" sx={{ mb: 2, color: '#c9a227', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WineBar /> 今日酒單
                </Typography>

                <Grid container spacing={2}>
                    {wines.map((wine) => (
                        <Grid item xs={12} key={wine.id}>
                            <Card sx={{ display: 'flex', bgcolor: '#2d2d2d', color: '#fff', borderRadius: 2 }}>
                                <CardMedia
                                    component="img"
                                    sx={{ width: 100, objectFit: 'contain', bgcolor: '#000' }}
                                    image={wine.image_url || 'https://via.placeholder.com/150'}
                                    alt={wine.name}
                                />
                                <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                                    <CardContent sx={{ flex: '1 0 auto', py: 1 }}>
                                        <Typography component="div" variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            {wine.name}
                                        </Typography>
                                        <Typography variant="subtitle2" color="#aaa" component="div">
                                            {wine.type}
                                        </Typography>
                                        <Box sx={{ mt: 1 }}>
                                            <Chip
                                                label={`${wine.vintage || 'NV'}`}
                                                size="small"
                                                sx={{ mr: 1, bgcolor: '#444', color: '#ccc' }}
                                            />
                                            <Chip
                                                label={wine.country || 'Unknown'}
                                                size="small"
                                                sx={{ bgcolor: '#444', color: '#ccc' }}
                                            />
                                        </Box>
                                    </CardContent>
                                </Box>
                            </Card>
                        </Grid>
                    ))}
                </Grid>

                {/* Action Button */}
                <Button
                    variant="contained"
                    fullWidth
                    size="large"
                    sx={{ mt: 5, bgcolor: '#c9a227', color: '#000', fontWeight: 'bold', borderRadius: 50 }}
                    onClick={() => {
                        // Add to Google Calendar logic or simple alert
                        alert("已收到您的回覆！期待見到您！");
                    }}
                >
                    我會參加 🍷
                </Button>
            </Box>
        </Box>
    );
};

export default InvitationDetail;
