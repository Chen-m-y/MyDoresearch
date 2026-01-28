import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Chip,
    useTheme
} from '@mui/material';

// 作者Chips组件 - 只显示一行，超出的用+X表示
function AuthorChips({ authors }) {
    const [visibleAuthors, setVisibleAuthors] = useState([]);
    const [hiddenCount, setHiddenCount] = useState(0);
    const containerRef = useRef(null);
    const theme = useTheme();

    useEffect(() => {
        if (!authors) return;

        const authorList = authors.split(',')
            .map(author => author.trim())
            .filter(author => author.length > 0);

        if (authorList.length === 0) return;

        // 创建临时容器来测量宽度
        const measureContainer = document.createElement('div');
        measureContainer.style.position = 'absolute';
        measureContainer.style.visibility = 'hidden';
        measureContainer.style.whiteSpace = 'nowrap';
        measureContainer.style.display = 'flex';
        measureContainer.style.gap = '2.4px'; // 对应gap: 0.3
        document.body.appendChild(measureContainer);

        // 获取容器可用宽度
        const containerWidth = containerRef.current?.offsetWidth || 300;
        let totalWidth = 0;
        let visibleCount = 0;

        // 逐个添加作者chip，测量宽度
        for (let i = 0; i < authorList.length; i++) {
            const chip = document.createElement('span');
            chip.style.cssText = `
                display: inline-flex;
                align-items: center;
                height: 18px;
                padding: 0 4px;
                font-size: 0.6rem;
                border: 1px solid ${theme.palette.primary.main}30;
                border-radius: 9px;
                background: linear-gradient(135deg, ${theme.palette.primary.main}08 0%, ${theme.palette.primary.main}15 100%);
            `;
            chip.textContent = authorList[i];
            measureContainer.appendChild(chip);

            const chipWidth = chip.offsetWidth;
            
            // 如果不是最后一个作者，需要为+X预留空间
            const remainingAuthors = authorList.length - i - 1;
            const plusChipWidth = remainingAuthors > 0 ? 40 : 0; // +X chip的大概宽度
            
            if (totalWidth + chipWidth + plusChipWidth > containerWidth - 10) {
                // 如果加上当前chip会超出，则停止
                break;
            }
            
            totalWidth += chipWidth + 2.4; // 加上gap
            visibleCount = i + 1;
        }

        document.body.removeChild(measureContainer);

        setVisibleAuthors(authorList.slice(0, visibleCount));
        setHiddenCount(Math.max(0, authorList.length - visibleCount));
    }, [authors, theme]);

    if (!authors) return null;

    return (
        <Box 
            component="span"
            ref={containerRef}
            sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 0.3,
                minHeight: 18,
                overflow: 'hidden'
            }}
        >
            {visibleAuthors.map((author, index) => (
                <Chip
                    key={index}
                    label={author}
                    size="small"
                    variant="outlined"
                    sx={{
                        height: 18,
                        fontSize: '0.6rem',
                        flexShrink: 0,
                        background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main}08 0%, ${theme.palette.primary.main}15 100%)`,
                        borderColor: (theme) => `${theme.palette.primary.main}30`,
                        color: (theme) => theme.palette.primary.main,
                        '& .MuiChip-label': {
                            px: 0.5,
                            py: 0
                        },
                        '&:hover': {
                            background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main}12 0%, ${theme.palette.primary.main}20 100%)`,
                            transform: 'translateY(-1px)',
                            boxShadow: (theme) => `0px 2px 4px ${theme.palette.primary.main}15`
                        },
                        transition: 'all 0.2s ease'
                    }}
                />
            ))}
            {hiddenCount > 0 && (
                <Chip
                    label={`+${hiddenCount}`}
                    size="small"
                    variant="outlined"
                    sx={{
                        height: 18,
                        fontSize: '0.6rem',
                        minWidth: 32,
                        flexShrink: 0,
                        background: (theme) => `linear-gradient(135deg, ${theme.palette.grey[100]} 0%, ${theme.palette.grey[200]} 100%)`,
                        borderColor: (theme) => `${theme.palette.grey[400]}60`,
                        color: (theme) => theme.palette.text.secondary,
                        '& .MuiChip-label': {
                            px: 0.5,
                            py: 0,
                            fontWeight: 600
                        },
                        '&:hover': {
                            background: (theme) => `linear-gradient(135deg, ${theme.palette.grey[200]} 0%, ${theme.palette.grey[300]} 100%)`,
                            transform: 'translateY(-1px)',
                            boxShadow: (theme) => `0px 2px 4px ${theme.palette.grey[400]}20`
                        },
                        transition: 'all 0.2s ease'
                    }}
                />
            )}
        </Box>
    );
}

export default AuthorChips;