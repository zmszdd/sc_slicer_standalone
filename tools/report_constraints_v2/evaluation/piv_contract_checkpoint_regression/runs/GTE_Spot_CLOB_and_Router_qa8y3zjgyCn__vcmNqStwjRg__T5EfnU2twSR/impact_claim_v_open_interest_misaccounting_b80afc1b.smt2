; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c20bb46df_new_order_appended () Bool)
(declare-fun c20bb46df_non_head_order_exists () Bool)
(declare-fun c20bb46df_open_interest_matches_reachable () Bool)
(declare-fun c20bb46df_open_interest_misaccounted () Bool)
(declare-fun c20bb46df_order_addressable_via_chain () Bool)
(assert
 (= c20bb46df_new_order_appended c20bb46df_new_order_appended))
(assert
 (= c20bb46df_non_head_order_exists c20bb46df_non_head_order_exists))
(assert
 (= c20bb46df_open_interest_matches_reachable c20bb46df_open_interest_matches_reachable))
(assert
 (= c20bb46df_open_interest_misaccounted c20bb46df_open_interest_misaccounted))
(assert
 (= c20bb46df_order_addressable_via_chain c20bb46df_order_addressable_via_chain))
(define-fun report_preconditions () Bool (and c20bb46df_non_head_order_exists c20bb46df_new_order_appended))
(define-fun report_safety () Bool (=> (and c20bb46df_non_head_order_exists c20bb46df_new_order_appended)
    (and c20bb46df_order_addressable_via_chain
         c20bb46df_open_interest_matches_reachable
         (not c20bb46df_open_interest_misaccounted))))
(define-fun report_effects () Bool (and c20bb46df_non_head_order_exists
     c20bb46df_new_order_appended
     (not (and c20bb46df_order_addressable_via_chain
               c20bb46df_open_interest_matches_reachable
               (not c20bb46df_open_interest_misaccounted)))))
