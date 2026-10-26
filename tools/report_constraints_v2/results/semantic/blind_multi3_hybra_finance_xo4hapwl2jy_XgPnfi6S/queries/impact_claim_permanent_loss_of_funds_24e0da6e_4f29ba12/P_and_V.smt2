; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c34e9e84e_ghybr_shares_burned () Bool)
(declare-fun c34e9e84e_shares_burned_without_exit () Bool)
(declare-fun c34e9e84e_underlying_hybr_claimable () Bool)
(declare-fun c34e9e84e_user_controls_full_ghybr_supply () Bool)
(declare-fun c34e9e84e_user_owns_full_venft_value () Bool)
(declare-fun c34e9e84e_withdrawal_completes () Bool)
(assert
 (= c34e9e84e_ghybr_shares_burned c34e9e84e_ghybr_shares_burned))
(assert
 (= c34e9e84e_shares_burned_without_exit c34e9e84e_shares_burned_without_exit))
(assert
 (= c34e9e84e_underlying_hybr_claimable c34e9e84e_underlying_hybr_claimable))
(assert
 (= c34e9e84e_user_controls_full_ghybr_supply c34e9e84e_user_controls_full_ghybr_supply))
(assert
 (= c34e9e84e_user_owns_full_venft_value c34e9e84e_user_owns_full_venft_value))
(assert
 (= c34e9e84e_withdrawal_completes c34e9e84e_withdrawal_completes))
(define-fun report_preconditions () Bool (and c34e9e84e_user_controls_full_ghybr_supply
     c34e9e84e_user_owns_full_venft_value))
(define-fun report_safety () Bool (=> c34e9e84e_ghybr_shares_burned
    (and c34e9e84e_withdrawal_completes c34e9e84e_underlying_hybr_claimable)))
(define-fun report_effects () Bool (and c34e9e84e_ghybr_shares_burned
     (not c34e9e84e_withdrawal_completes)
     (not c34e9e84e_underlying_hybr_claimable)
     c34e9e84e_shares_burned_without_exit))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
