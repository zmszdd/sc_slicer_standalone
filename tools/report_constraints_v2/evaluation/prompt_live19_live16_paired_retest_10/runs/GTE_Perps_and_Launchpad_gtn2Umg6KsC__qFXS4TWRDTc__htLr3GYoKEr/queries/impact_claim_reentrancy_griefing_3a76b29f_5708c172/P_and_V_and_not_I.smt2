; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cca301e46_launch_asset_amount_nonzero () Bool)
(declare-fun cca301e46_reentrancy_window_created () Bool)
(declare-fun cca301e46_reentry_during_transferfrom () Bool)
(declare-fun cca301e46_token_executes_code_during_transfer () Bool)
(assert
 (= cca301e46_launch_asset_amount_nonzero cca301e46_launch_asset_amount_nonzero))
(assert
 (= cca301e46_reentrancy_window_created cca301e46_reentrancy_window_created))
(assert
 (= cca301e46_reentry_during_transferfrom cca301e46_reentry_during_transferfrom))
(assert
 (= cca301e46_token_executes_code_during_transfer cca301e46_token_executes_code_during_transfer))
(define-fun report_preconditions () Bool (and cca301e46_launch_asset_amount_nonzero
     cca301e46_token_executes_code_during_transfer))
(define-fun report_safety () Bool (=> cca301e46_reentrancy_window_created
    (=> (and cca301e46_launch_asset_amount_nonzero
             cca301e46_token_executes_code_during_transfer)
        (not cca301e46_reentry_during_transferfrom))))
(define-fun report_effects () Bool (and cca301e46_reentrancy_window_created
     cca301e46_launch_asset_amount_nonzero
     cca301e46_token_executes_code_during_transfer
     (not (not cca301e46_reentry_during_transferfrom))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
