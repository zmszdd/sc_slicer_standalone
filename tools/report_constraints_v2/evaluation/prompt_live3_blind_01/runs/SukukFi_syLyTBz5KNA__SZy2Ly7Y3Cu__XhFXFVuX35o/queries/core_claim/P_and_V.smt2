; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun self_allowance_enabled () Bool)
(declare-fun victim_has_shares () Bool)
(declare-fun caller_is_owner_or_approved () Bool)
(declare-fun victim_shares_burned () Bool)
(assert
 (= self_allowance_enabled self_allowance_enabled))
(assert
 (= victim_has_shares victim_has_shares))
(assert
 (= caller_is_owner_or_approved caller_is_owner_or_approved))
(assert
 (= victim_shares_burned victim_shares_burned))
(define-fun report_preconditions () Bool (and self_allowance_enabled victim_has_shares))
(define-fun report_safety () Bool (=> (and self_allowance_enabled
         victim_has_shares
         (not caller_is_owner_or_approved))
    (not victim_shares_burned)))
(define-fun report_effects () Bool (and self_allowance_enabled
     victim_has_shares
     (not caller_is_owner_or_approved)
     (not (not victim_shares_burned))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
