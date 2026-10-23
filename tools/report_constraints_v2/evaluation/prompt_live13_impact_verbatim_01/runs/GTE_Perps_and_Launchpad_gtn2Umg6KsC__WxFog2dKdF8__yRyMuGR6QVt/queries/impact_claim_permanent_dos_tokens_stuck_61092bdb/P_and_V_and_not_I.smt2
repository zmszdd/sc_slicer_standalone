; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9042c30f_createpair_salt_param_count () Int)
(declare-fun c9042c30f_graduation_reaches_liquidity_phase () Bool)
(declare-fun c9042c30f_pairfor_salt_param_count () Int)
(declare-fun c9042c30f_skim_target_is_existing_pair () Bool)
(declare-fun c9042c30f_tokens_stuck_in_bonding_phase () Bool)
(assert
 (= c9042c30f_createpair_salt_param_count c9042c30f_createpair_salt_param_count))
(assert
 (= c9042c30f_graduation_reaches_liquidity_phase c9042c30f_graduation_reaches_liquidity_phase))
(assert
 (= c9042c30f_pairfor_salt_param_count c9042c30f_pairfor_salt_param_count))
(assert
 (= c9042c30f_skim_target_is_existing_pair c9042c30f_skim_target_is_existing_pair))
(assert
 (= c9042c30f_tokens_stuck_in_bonding_phase c9042c30f_tokens_stuck_in_bonding_phase))
(define-fun report_preconditions () Bool (and c9042c30f_graduation_reaches_liquidity_phase
     (= 2 c9042c30f_pairfor_salt_param_count)
     (= 4 c9042c30f_createpair_salt_param_count)))
(define-fun report_safety () Bool (=> (and c9042c30f_graduation_reaches_liquidity_phase
         (= 2 c9042c30f_pairfor_salt_param_count)
         (= 4 c9042c30f_createpair_salt_param_count))
    (and c9042c30f_skim_target_is_existing_pair
         (not c9042c30f_tokens_stuck_in_bonding_phase))))
(define-fun report_effects () Bool (and c9042c30f_graduation_reaches_liquidity_phase
     (= 2 c9042c30f_pairfor_salt_param_count)
     (= 4 c9042c30f_createpair_salt_param_count)
     (not (and c9042c30f_skim_target_is_existing_pair
               (not c9042c30f_tokens_stuck_in_bonding_phase)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
