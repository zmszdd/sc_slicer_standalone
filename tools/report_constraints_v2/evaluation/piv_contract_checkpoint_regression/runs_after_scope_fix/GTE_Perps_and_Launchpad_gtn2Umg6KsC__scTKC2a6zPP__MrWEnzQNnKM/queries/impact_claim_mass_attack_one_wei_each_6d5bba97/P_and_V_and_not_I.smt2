; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc8199e4b_graduation_completes () Bool)
(declare-fun cc8199e4b_mass_attack_occurs () Bool)
(declare-fun cc8199e4b_pair_deployed_before_graduation () Bool)
(declare-fun cc8199e4b_token_near_graduation () Bool)
(assert
 (= cc8199e4b_graduation_completes cc8199e4b_graduation_completes))
(assert
 (= cc8199e4b_mass_attack_occurs cc8199e4b_mass_attack_occurs))
(assert
 (= cc8199e4b_pair_deployed_before_graduation cc8199e4b_pair_deployed_before_graduation))
(assert
 (= cc8199e4b_token_near_graduation cc8199e4b_token_near_graduation))
(define-fun report_preconditions () Bool (and cc8199e4b_token_near_graduation cc8199e4b_pair_deployed_before_graduation))
(define-fun report_safety () Bool (=> (and cc8199e4b_token_near_graduation
         cc8199e4b_pair_deployed_before_graduation)
    (and cc8199e4b_graduation_completes (not cc8199e4b_mass_attack_occurs))))
(define-fun report_effects () Bool (and cc8199e4b_token_near_graduation
     cc8199e4b_pair_deployed_before_graduation
     (not (and cc8199e4b_graduation_completes
               (not cc8199e4b_mass_attack_occurs)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
