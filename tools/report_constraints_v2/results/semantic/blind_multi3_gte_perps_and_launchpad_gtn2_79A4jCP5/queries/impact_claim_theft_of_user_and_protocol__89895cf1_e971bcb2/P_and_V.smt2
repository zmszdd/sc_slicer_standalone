; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca95ede88_direct_mint_without_pre_transfer () Bool)
(declare-fun ca95ede88_lp_minted_for_free () Bool)
(declare-fun ca95ede88_total_launchpad_fee0_nonzero () Bool)
(declare-fun ca95ede88_total_launchpad_fee1_nonzero () Bool)
(assert
 (= ca95ede88_direct_mint_without_pre_transfer ca95ede88_direct_mint_without_pre_transfer))
(assert
 (= ca95ede88_lp_minted_for_free ca95ede88_lp_minted_for_free))
(assert
 (= ca95ede88_total_launchpad_fee0_nonzero ca95ede88_total_launchpad_fee0_nonzero))
(assert
 (= ca95ede88_total_launchpad_fee1_nonzero ca95ede88_total_launchpad_fee1_nonzero))
(define-fun report_preconditions () Bool (and ca95ede88_total_launchpad_fee0_nonzero
     ca95ede88_total_launchpad_fee1_nonzero
     ca95ede88_direct_mint_without_pre_transfer))
(define-fun report_safety () Bool (=> (and ca95ede88_total_launchpad_fee0_nonzero
         ca95ede88_total_launchpad_fee1_nonzero)
    (not ca95ede88_lp_minted_for_free)))
(define-fun report_effects () Bool ca95ede88_lp_minted_for_free)
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
