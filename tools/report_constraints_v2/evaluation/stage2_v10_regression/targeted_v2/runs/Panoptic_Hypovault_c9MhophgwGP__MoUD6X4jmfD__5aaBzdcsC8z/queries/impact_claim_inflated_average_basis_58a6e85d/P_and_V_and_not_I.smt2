; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c192231ea_alice_basis_before () Int)
(declare-fun c192231ea_alice_basis_merged () Int)
(declare-fun c192231ea_alice_market_value () Int)
(declare-fun c192231ea_bob_basis_incoming () Int)
(declare-fun c192231ea_collusion_occurred () Bool)
(assert
 (= c192231ea_alice_basis_before c192231ea_alice_basis_before))
(assert
 (= c192231ea_alice_basis_merged c192231ea_alice_basis_merged))
(assert
 (= c192231ea_alice_market_value c192231ea_alice_market_value))
(assert
 (= c192231ea_bob_basis_incoming c192231ea_bob_basis_incoming))
(assert
 (= c192231ea_collusion_occurred c192231ea_collusion_occurred))
(define-fun report_preconditions () Bool (and (> c192231ea_alice_market_value c192231ea_alice_basis_before)
     (> c192231ea_bob_basis_incoming c192231ea_alice_market_value)
     c192231ea_collusion_occurred))
(define-fun report_safety () Bool (=> (= c192231ea_alice_basis_merged
       (+ c192231ea_alice_basis_before c192231ea_bob_basis_incoming))
    (=> (and (> c192231ea_alice_market_value c192231ea_alice_basis_before)
             (> c192231ea_bob_basis_incoming c192231ea_alice_market_value)
             c192231ea_collusion_occurred)
        (< c192231ea_alice_basis_merged c192231ea_alice_market_value))))
(define-fun report_effects () Bool (and (= c192231ea_alice_basis_merged
        (+ c192231ea_alice_basis_before c192231ea_bob_basis_incoming))
     (> c192231ea_alice_market_value c192231ea_alice_basis_before)
     (> c192231ea_bob_basis_incoming c192231ea_alice_market_value)
     c192231ea_collusion_occurred
     (not (< c192231ea_alice_basis_merged c192231ea_alice_market_value))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
