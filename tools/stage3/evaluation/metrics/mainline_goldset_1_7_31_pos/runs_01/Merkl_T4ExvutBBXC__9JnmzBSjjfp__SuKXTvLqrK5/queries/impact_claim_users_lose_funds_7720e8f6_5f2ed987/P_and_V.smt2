; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce790d90e_fot_fee_deducted_on_transfer () Bool)
(declare-fun ce790d90e_fot_rejected_or_documented_before_whitelist () Bool)
(declare-fun ce790d90e_fot_token_whitelisted () Bool)
(declare-fun ce790d90e_users_lose_funds_occurred () Bool)
(assert
 (= ce790d90e_fot_fee_deducted_on_transfer ce790d90e_fot_fee_deducted_on_transfer))
(assert
 (= ce790d90e_fot_rejected_or_documented_before_whitelist ce790d90e_fot_rejected_or_documented_before_whitelist))
(assert
 (= ce790d90e_fot_token_whitelisted ce790d90e_fot_token_whitelisted))
(assert
 (= ce790d90e_users_lose_funds_occurred ce790d90e_users_lose_funds_occurred))
(define-fun report_preconditions () Bool (and ce790d90e_fot_token_whitelisted ce790d90e_fot_fee_deducted_on_transfer))
(define-fun report_safety () Bool (=> ce790d90e_fot_token_whitelisted
    ce790d90e_fot_rejected_or_documented_before_whitelist))
(define-fun report_effects () Bool (and ce790d90e_fot_token_whitelisted
     (not ce790d90e_fot_rejected_or_documented_before_whitelist)
     ce790d90e_users_lose_funds_occurred))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
