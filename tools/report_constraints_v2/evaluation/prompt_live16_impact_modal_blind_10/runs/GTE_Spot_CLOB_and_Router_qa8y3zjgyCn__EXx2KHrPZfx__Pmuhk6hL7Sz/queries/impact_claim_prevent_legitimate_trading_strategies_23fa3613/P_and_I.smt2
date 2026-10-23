; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c88d17d80_expired_order_placed_at_top_of_book () Bool)
(declare-fun c88d17d80_expired_order_remains_in_price_tree () Bool)
(declare-fun c88d17d80_legitimate_strategy_functioning () Bool)
(declare-fun c88d17d80_new_post_only_at_same_or_better_price () Bool)
(declare-fun c88d17d80_post_only_rejected_as_would_fill () Bool)
(declare-fun c88d17d80_would_match_non_expired_order () Bool)
(assert
 (= c88d17d80_expired_order_placed_at_top_of_book c88d17d80_expired_order_placed_at_top_of_book))
(assert
 (= c88d17d80_expired_order_remains_in_price_tree c88d17d80_expired_order_remains_in_price_tree))
(assert
 (= c88d17d80_legitimate_strategy_functioning c88d17d80_legitimate_strategy_functioning))
(assert
 (= c88d17d80_new_post_only_at_same_or_better_price c88d17d80_new_post_only_at_same_or_better_price))
(assert
 (= c88d17d80_post_only_rejected_as_would_fill c88d17d80_post_only_rejected_as_would_fill))
(assert
 (= c88d17d80_would_match_non_expired_order c88d17d80_would_match_non_expired_order))
(define-fun report_preconditions () Bool (and c88d17d80_expired_order_placed_at_top_of_book
     c88d17d80_expired_order_remains_in_price_tree
     c88d17d80_new_post_only_at_same_or_better_price))
(define-fun report_safety () Bool (=> (and c88d17d80_expired_order_placed_at_top_of_book
         c88d17d80_expired_order_remains_in_price_tree
         c88d17d80_new_post_only_at_same_or_better_price
         (not c88d17d80_would_match_non_expired_order))
    (and (not c88d17d80_post_only_rejected_as_would_fill)
         c88d17d80_legitimate_strategy_functioning)))
(define-fun report_effects () Bool (and c88d17d80_expired_order_placed_at_top_of_book
     c88d17d80_expired_order_remains_in_price_tree
     c88d17d80_new_post_only_at_same_or_better_price
     (not c88d17d80_would_match_non_expired_order)
     (not (and (not c88d17d80_post_only_rejected_as_would_fill)
               c88d17d80_legitimate_strategy_functioning))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
