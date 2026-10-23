; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c20bb46df_non_head_order_cancelled_or_matched () Bool)
(declare-fun c20bb46df_open_interest_misaccounted () Bool)
(declare-fun c20bb46df_open_interest_reflects_reachable_only () Bool)
(declare-fun c20bb46df_order_addressable_via_chain () Bool)
(declare-fun c20bb46df_stored_prev_order_id () Int)
(assert
 (= c20bb46df_non_head_order_cancelled_or_matched c20bb46df_non_head_order_cancelled_or_matched))
(assert
 (= c20bb46df_open_interest_misaccounted c20bb46df_open_interest_misaccounted))
(assert
 (= c20bb46df_open_interest_reflects_reachable_only c20bb46df_open_interest_reflects_reachable_only))
(assert
 (= c20bb46df_order_addressable_via_chain c20bb46df_order_addressable_via_chain))
(assert
 (= c20bb46df_stored_prev_order_id c20bb46df_stored_prev_order_id))
(define-fun report_preconditions () Bool (and (= 0 c20bb46df_stored_prev_order_id)
     c20bb46df_non_head_order_cancelled_or_matched))
(define-fun report_safety () Bool (=> (and (= 0 c20bb46df_stored_prev_order_id)
         c20bb46df_non_head_order_cancelled_or_matched)
    (and c20bb46df_order_addressable_via_chain
         c20bb46df_open_interest_reflects_reachable_only
         (not c20bb46df_open_interest_misaccounted))))
(define-fun report_effects () Bool (and (= 0 c20bb46df_stored_prev_order_id)
     c20bb46df_non_head_order_cancelled_or_matched
     (not (and c20bb46df_order_addressable_via_chain
               c20bb46df_open_interest_reflects_reachable_only
               (not c20bb46df_open_interest_misaccounted)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
