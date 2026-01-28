-- Performance optimization index for subscription papers query
-- Reduces query time from ~155ms to ~1ms (150x improvement)

CREATE INDEX IF NOT EXISTS idx_papers_subscription_published_created 
ON papers(subscription_id, published_date DESC, created_at DESC);

-- This composite index optimizes the most common subscription papers query:
-- SELECT * FROM papers WHERE subscription_id = ? ORDER BY published_date DESC, created_at DESC LIMIT ? OFFSET ?