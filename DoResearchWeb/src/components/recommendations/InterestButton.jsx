import React, { useState } from 'react';
import {
    IconButton,
    Tooltip,
    Box,
    Snackbar,
    Alert
} from '@mui/material';
import {
    ThumbUp as ThumbUpIcon,
    ThumbDown as ThumbDownIcon,
    ThumbUpOutlined as ThumbUpOutlinedIcon,
    ThumbDownOutlined as ThumbDownOutlinedIcon
} from '@mui/icons-material';
import apiClient from '../../services/apiClient.jsx';

/**
 * 兴趣度评价按钮组件
 * 用于用户明确表示对论文的喜好
 */
const InterestButton = ({ 
    paperId, 
    size = 'small',
    showBoth = true,
    color = 'default',
    onInterestMarked = null
}) => {
    const [liked, setLiked] = useState(false);
    const [disliked, setDisliked] = useState(false);
    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    
    // 直接使用新的 API 而不是通过 tracker

    // 处理喜欢点击
    const handleLike = async (event) => {
        event.stopPropagation(); // 防止冒泡到父组件
        
        if (liked) return; // 已经点赞过了

        setLoading(true);
        try {
            await apiClient.markInterest({ paper_id: paperId, interest_type: 'like' });
            setLiked(true);
            setDisliked(false); // 取消不喜欢
            
            setNotification({
                open: true,
                message: '已标记为感兴趣',
                severity: 'success'
            });

            if (onInterestMarked) {
                onInterestMarked(paperId, 'like');
            }
        } catch (error) {
            console.error('标记兴趣失败:', error);
            setNotification({
                open: true,
                message: '标记失败，请重试',
                severity: 'error'
            });
        } finally {
            setLoading(false);
        }
    };

    // 处理不喜欢点击
    const handleDislike = async (event) => {
        event.stopPropagation(); // 防止冒泡到父组件
        
        if (disliked) return; // 已经标记过了

        setLoading(true);
        try {
            await apiClient.markInterest({ paper_id: paperId, interest_type: 'dislike' });
            setDisliked(true);
            setLiked(false); // 取消喜欢
            
            setNotification({
                open: true,
                message: '已标记为不感兴趣',
                severity: 'info'
            });

            if (onInterestMarked) {
                onInterestMarked(paperId, 'dislike');
            }
        } catch (error) {
            console.error('标记兴趣失败:', error);
            setNotification({
                open: true,
                message: '标记失败，请重试',
                severity: 'error'
            });
        } finally {
            setLoading(false);
        }
    };

    // 关闭通知
    const handleCloseNotification = () => {
        setNotification({ ...notification, open: false });
    };

    return (
        <>
            <Box display="flex" alignItems="center">
                {/* 喜欢按钮 */}
                <Tooltip title={liked ? '已标记为感兴趣' : '标记为感兴趣'}>
                    <IconButton
                        onClick={handleLike}
                        disabled={loading}
                        size={size}
                        color={liked ? 'success' : color}
                        sx={{
                            '&:hover': {
                                color: 'success.main',
                                transform: 'scale(1.1)'
                            },
                            transition: 'all 0.2s ease-in-out'
                        }}
                    >
                        {liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
                    </IconButton>
                </Tooltip>

                {/* 不喜欢按钮 */}
                {showBoth && (
                    <Tooltip title={disliked ? '已标记为不感兴趣' : '标记为不感兴趣'}>
                        <IconButton
                            onClick={handleDislike}
                            disabled={loading}
                            size={size}
                            color={disliked ? 'error' : color}
                            sx={{
                                ml: 0.5,
                                '&:hover': {
                                    color: 'error.main',
                                    transform: 'scale(1.1)'
                                },
                                transition: 'all 0.2s ease-in-out'
                            }}
                        >
                            {disliked ? <ThumbDownIcon /> : <ThumbDownOutlinedIcon />}
                        </IconButton>
                    </Tooltip>
                )}
            </Box>

            {/* 通知消息 */}
            <Snackbar
                open={notification.open}
                autoHideDuration={3000}
                onClose={handleCloseNotification}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert 
                    onClose={handleCloseNotification} 
                    severity={notification.severity}
                    variant="filled"
                    sx={{ width: '100%' }}
                >
                    {notification.message}
                </Alert>
            </Snackbar>
        </>
    );
};

export default InterestButton;