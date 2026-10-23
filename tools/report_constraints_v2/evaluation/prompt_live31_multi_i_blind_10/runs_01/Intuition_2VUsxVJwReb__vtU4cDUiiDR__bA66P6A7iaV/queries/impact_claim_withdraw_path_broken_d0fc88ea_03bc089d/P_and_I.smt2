; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c56972c08_half_slope_times_total_shares_squared () Int)
(declare-fun c56972c08_helper_usage_assumed () Bool)
(declare-fun c56972c08_preview_withdraw_reverted () Bool)
(declare-fun c56972c08_realistic_deposit_occurred () Bool)
(declare-fun c56972c08_total_assets_after_deposit () Int)
(assert
 (= c56972c08_half_slope_times_total_shares_squared c56972c08_half_slope_times_total_shares_squared))
(assert
 (= c56972c08_helper_usage_assumed c56972c08_helper_usage_assumed))
(assert
 (= c56972c08_preview_withdraw_reverted c56972c08_preview_withdraw_reverted))
(assert
 (= c56972c08_realistic_deposit_occurred c56972c08_realistic_deposit_occurred))
(assert
 (= c56972c08_total_assets_after_deposit c56972c08_total_assets_after_deposit))
(define-fun report_preconditions () Bool (and c56972c08_realistic_deposit_occurred
     (> c56972c08_total_assets_after_deposit
        c56972c08_half_slope_times_total_shares_squared)
     c56972c08_helper_usage_assumed))
(define-fun report_safety () Bool (=> c56972c08_preview_withdraw_reverted
    (=> (and c56972c08_realistic_deposit_occurred
             (> c56972c08_total_assets_after_deposit
                c56972c08_half_slope_times_total_shares_squared)
             c56972c08_helper_usage_assumed)
        (not c56972c08_preview_withdraw_reverted))))
(define-fun report_effects () Bool (and c56972c08_preview_withdraw_reverted
     c56972c08_realistic_deposit_occurred
     (> c56972c08_total_assets_after_deposit
        c56972c08_half_slope_times_total_shares_squared)
     c56972c08_helper_usage_assumed
     (not (not c56972c08_preview_withdraw_reverted))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
