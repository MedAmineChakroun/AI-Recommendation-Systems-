SELECT
  countIf(event = 'Product CF Clicked') AS clicks,
  countIf(event = 'Product CF Impression') AS impressions,
  clicks / impressions AS ctr
FROM events
WHERE timestamp >= now() - INTERVAL 7 DAY