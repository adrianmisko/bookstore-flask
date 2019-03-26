CREATE OR REPLACE FUNCTION get_pricing(
	IN _book_id INT,
	OUT product_pricing_valid_until TIMESTAMP WITHOUT TIME ZONE,
 	OUT product_pricing_discount_value NUMERIC,
 	OUT product_pricing_discount_percent INTEGER,
 	OUT category_discount_valid_until TIMESTAMP WITHOUT TIME ZONE,
 	OUT category_discount_discount_value NUMERIC,
 	OUT category_discount_discount_percent INTEGER,
	OUT category_name VARCHAR
) AS $$
BEGIN
	SELECT 
 		pp.valid_until, pp.discount_value, pp.discount_percent
 	INTO 
 		product_pricing_valid_until, product_pricing_discount_value, product_pricing_discount_percent
 	FROM 
 		product_pricing pp
 	WHERE
 		pp.book_id = _book_id
 	 			AND
 		CURRENT_TIMESTAMP BETWEEN pp.valid_from AND pp.valid_until 
 	ORDER BY
 		pp.valid_from DESC;

 	SELECT 
 		cd.valid_until, cd.discount_value, cd.discount_percent, cd.genre_name
 	INTO 
 		category_discount_valid_until, category_discount_discount_value, category_discount_discount_percent, category_name
 	FROM 
 		category_discount cd JOIN genre g ON (g.name = cd.genre_name) JOIN books_genres bg ON (g.name = bg.genre_name)
 	WHERE
 		bg.book_id = _book_id
 			AND
 		CURRENT_TIMESTAMP BETWEEN cd.valid_from AND cd.valid_until 
 	ORDER BY
 		cd.valid_from DESC;
END; $$ 
 
LANGUAGE 'plpgsql';

