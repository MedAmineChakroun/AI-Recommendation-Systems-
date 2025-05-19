SELECT
  countIf(event = 'recommendation_click') AS clicks,
  countIf(event = 'recommendation_impression') AS impressions,
  clicks / impressions AS ctr
FROM events
WHERE timestamp >= now() - INTERVAL 7 DAY