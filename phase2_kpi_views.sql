-- ─────────────────────────────────────────────
-- Airbnb Marketplace Analysis
-- Phase 2: KPI Views
-- Run these in MySQL Workbench after Phase 1
-- ─────────────────────────────────────────────

USE airbnb_analysis;

-- ─────────────────────────────────────────────
-- KPI 1: Average price per city
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_avg_price_by_city AS
SELECT
    city,
    ROUND(AVG(price), 2)        AS avg_price,
    ROUND(MIN(price), 2)        AS min_price,
    ROUND(MAX(price), 2)        AS max_price,
    COUNT(listing_id)           AS total_listings
FROM listings
WHERE price > 0 AND price < 10000   -- exclude outliers
GROUP BY city;


-- ─────────────────────────────────────────────
-- KPI 2: Occupancy rate per city
-- (occupancy = % of days NOT available)
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_occupancy_by_city AS
SELECT
    city,
    ROUND(
        (1 - AVG(available)) * 100, 2
    )                           AS occupancy_rate_pct,
    ROUND(AVG(available) * 100, 2) AS availability_rate_pct,
    COUNT(*)                    AS total_calendar_rows
FROM calendar
GROUP BY city;


-- ─────────────────────────────────────────────
-- KPI 3: Top 10 neighbourhoods by average price
-- (both cities combined, ranked)
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_top_neighbourhoods AS
SELECT
    city,
    neighbourhood,
    ROUND(AVG(price), 2)    AS avg_price,
    COUNT(listing_id)       AS num_listings
FROM listings
WHERE price > 0 AND price < 10000
  AND neighbourhood IS NOT NULL
GROUP BY city, neighbourhood
HAVING num_listings >= 10           -- only neighbourhoods with enough data
ORDER BY avg_price DESC;


-- ─────────────────────────────────────────────
-- KPI 4: Room type distribution
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_room_type_distribution AS
SELECT
    city,
    room_type,
    COUNT(listing_id)                               AS num_listings,
    ROUND(
        COUNT(listing_id) * 100.0 / SUM(COUNT(listing_id)) OVER (PARTITION BY city),
        1
    )                                               AS pct_of_city
FROM listings
WHERE room_type IS NOT NULL
GROUP BY city, room_type
ORDER BY city, num_listings DESC;


-- ─────────────────────────────────────────────
-- KPI 5: Estimated monthly revenue per listing
-- (avg_price * occupancy_days_per_month)
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_revenue_potential AS
SELECT
    l.city,
    l.listing_id,
    l.neighbourhood,
    l.room_type,
    l.price                                         AS listed_price,
    ROUND(
        l.price * (1 - AVG(c.available)) * 30, 2
    )                                               AS est_monthly_revenue
FROM listings l
JOIN calendar c ON l.listing_id = c.listing_id
WHERE l.price > 0 AND l.price < 10000
GROUP BY l.city, l.listing_id, l.neighbourhood, l.room_type, l.price;


-- ─────────────────────────────────────────────
-- SUMMARY VIEW: One table for Power BI overview
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_city_summary AS
SELECT
    p.city,
    p.avg_price,
    p.total_listings,
    o.occupancy_rate_pct,
    o.availability_rate_pct
FROM vw_avg_price_by_city p
JOIN vw_occupancy_by_city o ON p.city = o.city;


-- ─────────────────────────────────────────────
-- Quick check — run these to verify your views
-- ─────────────────────────────────────────────
-- SELECT * FROM vw_city_summary;
--   SELECT * FROM vw_top_neighbourhoods LIMIT 20;
--  SELECT * FROM vw_room_type_distribution;
--  SELECT * FROM vw_revenue_potential LIMIT 10;

UPDATE listings SET city = 'Amsterdam' WHERE city = 'amsterdam';
UPDATE listings SET city = 'Berlin' WHERE city = 'berlin';