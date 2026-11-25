; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8824baef_ask_tree_size_at_or_above_max () Bool)
(declare-fun c8824baef_limit_not_removed_observed () Bool)
(declare-fun c8824baef_new_order_introduces_new_limit () Bool)
(declare-fun c8824baef_non_competitive_order_removed () Bool)
(declare-fun c8824baef_worst_queue_order_count_gt_one () Bool)
(assert
 (= c8824baef_ask_tree_size_at_or_above_max c8824baef_ask_tree_size_at_or_above_max))
(assert
 (= c8824baef_limit_not_removed_observed c8824baef_limit_not_removed_observed))
(assert
 (= c8824baef_new_order_introduces_new_limit c8824baef_new_order_introduces_new_limit))
(assert
 (= c8824baef_non_competitive_order_removed c8824baef_non_competitive_order_removed))
(assert
 (= c8824baef_worst_queue_order_count_gt_one c8824baef_worst_queue_order_count_gt_one))
(define-fun report_preconditions () Bool (and c8824baef_ask_tree_size_at_or_above_max
     c8824baef_worst_queue_order_count_gt_one
     c8824baef_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> (and c8824baef_ask_tree_size_at_or_above_max
         c8824baef_worst_queue_order_count_gt_one
         c8824baef_new_order_introduces_new_limit)
    c8824baef_non_competitive_order_removed))
(define-fun report_effects () Bool (and c8824baef_ask_tree_size_at_or_above_max
     c8824baef_worst_queue_order_count_gt_one
     c8824baef_new_order_introduces_new_limit
     (not c8824baef_non_competitive_order_removed)
     c8824baef_limit_not_removed_observed))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
