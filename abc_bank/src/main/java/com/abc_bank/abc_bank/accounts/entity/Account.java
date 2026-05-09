package com.abc_bank.abc_bank.accounts.entity;


import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.enums.AccountStatus;
import com.abc_bank.abc_bank.enums.AccountType;
import com.abc_bank.abc_bank.enums.Currency;
import com.abc_bank.abc_bank.transaction.entity.Transaction;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Data
@Builder
@Table(name="accounts")
@AllArgsConstructor
@NoArgsConstructor
public class Account {
    @Id
    @GeneratedValue(strategy= GenerationType.IDENTITY)
    private Long id;

    @Column(nullable=false,unique=true,length=15)
    private String accountNumber;

    private BigDecimal BALANCE=BigDecimal.ZERO;

    @Enumerated(EnumType.STRING)
    @Column(nullable=false)
    private AccountType accountType;

    @ManyToOne(fetch=FetchType.LAZY)
    @JoinColumn(name="user_id", nullable=false)
    private User user;

    @Enumerated(EnumType.STRING)
    private Currency currency;

    @Enumerated(EnumType.STRING)
    private AccountStatus status;

    @OneToMany(mappedBy="account",cascade=CascadeType.ALL,orphanRemoval = true,fetch=FetchType.LAZY)
    private List<Transaction> transactions=new ArrayList<>();


    private LocalDateTime closedAt;
    private LocalDateTime createdAt=LocalDateTime.now();
    private LocalDateTime updatedAt;
}
