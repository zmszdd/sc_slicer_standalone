; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1b20e13a_bond_returned_to_disputer () Bool)
(declare-fun c1b20e13a_dispute_is_valid () Bool)
(declare-fun c1b20e13a_dispute_posted () Bool)
(declare-fun c1b20e13a_disputer_blacklisted () Bool)
(declare-fun c1b20e13a_token_has_blacklist () Bool)
(assert
 (= c1b20e13a_bond_returned_to_disputer c1b20e13a_bond_returned_to_disputer))
(assert
 (= c1b20e13a_dispute_is_valid c1b20e13a_dispute_is_valid))
(assert
 (= c1b20e13a_dispute_posted c1b20e13a_dispute_posted))
(assert
 (= c1b20e13a_disputer_blacklisted c1b20e13a_disputer_blacklisted))
(assert
 (= c1b20e13a_token_has_blacklist c1b20e13a_token_has_blacklist))
(define-fun report_preconditions () Bool (and c1b20e13a_dispute_posted
     c1b20e13a_token_has_blacklist
     c1b20e13a_disputer_blacklisted
     c1b20e13a_dispute_is_valid))
(define-fun report_safety () Bool (=> (and c1b20e13a_dispute_posted c1b20e13a_dispute_is_valid)
    c1b20e13a_bond_returned_to_disputer))
(define-fun report_effects () Bool (and c1b20e13a_dispute_posted
     c1b20e13a_dispute_is_valid
     (not c1b20e13a_bond_returned_to_disputer)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
