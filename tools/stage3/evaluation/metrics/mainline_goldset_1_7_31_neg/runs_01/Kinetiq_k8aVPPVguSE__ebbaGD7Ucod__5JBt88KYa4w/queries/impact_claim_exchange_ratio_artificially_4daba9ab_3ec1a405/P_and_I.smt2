; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf20ce2ea_exchange_ratio_basis_hype () Int)
(declare-fun cf20ce2ea_exchange_ratio_lowered () Bool)
(declare-fun cf20ce2ea_slashed_funds_present () Bool)
(declare-fun cf20ce2ea_staking_limit_basis_hype () Int)
(assert
 (= cf20ce2ea_exchange_ratio_basis_hype cf20ce2ea_exchange_ratio_basis_hype))
(assert
 (= cf20ce2ea_exchange_ratio_lowered cf20ce2ea_exchange_ratio_lowered))
(assert
 (= cf20ce2ea_slashed_funds_present cf20ce2ea_slashed_funds_present))
(assert
 (= cf20ce2ea_staking_limit_basis_hype cf20ce2ea_staking_limit_basis_hype))
(define-fun report_preconditions () Bool cf20ce2ea_slashed_funds_present)
(define-fun report_safety () Bool (=> cf20ce2ea_slashed_funds_present
    (= cf20ce2ea_staking_limit_basis_hype cf20ce2ea_exchange_ratio_basis_hype)))
(define-fun report_effects () Bool (and cf20ce2ea_slashed_funds_present
     (not (= cf20ce2ea_staking_limit_basis_hype
             cf20ce2ea_exchange_ratio_basis_hype))
     cf20ce2ea_exchange_ratio_lowered))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
